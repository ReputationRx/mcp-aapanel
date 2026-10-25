"""Copy Docker images from this aaPanel host to another one.

Image layers occupy disk. Running containers occupy RAM. Transfer streams
`docker save` into `docker load` on the destination so the source does not
need a second full copy of the image on disk.
"""

import json
import os
import re
import shlex
import subprocess
import threading
from typing import Dict, List, Optional

IMAGE_REF_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}$')
HOST_RE = re.compile(r'^[A-Za-z0-9]([A-Za-z0-9.-]{0,252}[A-Za-z0-9])?$')
USER_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9._-]{0,31}$')
TARGET_RE = re.compile(r'^[A-Za-z0-9_-]{1,64}$')
SSH_KEY_RE = re.compile(r'^/[A-Za-z0-9._/-]{1,4096}$')
IMAGE_ID_RE = re.compile(r'^[a-fA-F0-9]{12,64}$')
CONTAINER_ID_RE = re.compile(r'^[a-fA-F0-9]{12,64}$')

NOT_TRANSFERRED = [
    "container configuration",
    "volumes and bind mounts",
    "networks",
    "environment variables",
]

MAX_IMAGES = 20
INSPECT_BATCH = 50


class DockerImageError(Exception):
    """Caller-facing failure that is safe to return as an error string."""


def format_bytes(num: int) -> str:
    size = float(num)
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if size < 1024 or unit == 'TB':
            if unit == 'B':
                return f'{int(size)} B'
            return f'{size:.1f} {unit}'
        size /= 1024
    return f'{int(num)} B'


def validate_image_ref(image: str) -> str:
    if not isinstance(image, str) or not IMAGE_REF_RE.fullmatch(image):
        raise DockerImageError(f"invalid image reference: {image!r}")
    if '..' in image or '//' in image or image.startswith('-'):
        raise DockerImageError(f"invalid image reference: {image!r}")
    return image


def normalize_images(images) -> List[str]:
    if isinstance(images, str):
        images = [images]
    if not isinstance(images, list) or not images:
        raise DockerImageError("images must be a non-empty list of image names")
    if len(images) > MAX_IMAGES:
        raise DockerImageError(f"transfer at most {MAX_IMAGES} images at a time")
    seen = []
    for image in images:
        ref = validate_image_ref(image)
        if ref not in seen:
            seen.append(ref)
    return seen


def _flag(value, default: bool = False) -> bool:
    if value is None:
        return default
    if not isinstance(value, bool):
        raise DockerImageError("expected true or false")
    return value


def _timeout_seconds(value) -> int:
    if value is None:
        return 3600
    if isinstance(value, bool) or not isinstance(value, int):
        raise DockerImageError("timeout_seconds must be an integer")
    if value < 30 or value > 86400:
        raise DockerImageError("timeout_seconds must be between 30 and 86400")
    return value


def _port(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise DockerImageError("port must be an integer")
    if value < 1 or value > 65535:
        raise DockerImageError("port must be between 1 and 65535")
    return value


def _clip(text: str, limit: int = 4000) -> str:
    if text is None:
        return ''
    if len(text) <= limit:
        return text
    return text[:limit] + '...<truncated>'


def resolve_destination(params: Dict, targets: Dict) -> Dict:
    if not isinstance(params, dict):
        raise DockerImageError("params must be an object")
    targets = targets if isinstance(targets, dict) else {}
    base = {}
    target_name = params.get('target')
    if target_name is not None:
        if not isinstance(target_name, str) or not TARGET_RE.fullmatch(target_name):
            raise DockerImageError("target name is invalid")
        selected = targets.get(target_name)
        if not isinstance(selected, dict):
            raise DockerImageError(f"unknown docker target: {target_name}")
        base = selected

    host = params.get('host', base.get('host'))
    user = params.get('user', base.get('user', 'root'))
    port = params.get('port', base.get('port', 22))
    ssh_key = params.get('ssh_key', base.get('ssh_key'))
    if 'use_sudo' in params:
        use_sudo = params.get('use_sudo')
    else:
        use_sudo = base.get('use_sudo', False)

    if not isinstance(host, str) or not HOST_RE.fullmatch(host) or '..' in host:
        raise DockerImageError("destination host is missing or invalid")
    if not isinstance(user, str) or not USER_RE.fullmatch(user):
        raise DockerImageError("destination user is invalid")
    if ssh_key in ('', None):
        ssh_key = None
    elif not isinstance(ssh_key, str) or not SSH_KEY_RE.fullmatch(ssh_key) or '..' in ssh_key:
        raise DockerImageError("ssh_key path is invalid")
    elif not os.path.isfile(ssh_key):
        raise DockerImageError(f"ssh_key file does not exist: {ssh_key}")

    return {
        "host": host,
        "user": user,
        "port": _port(port),
        "ssh_key": ssh_key,
        "use_sudo": _flag(use_sudo, False),
    }


def public_destination(dest: Dict) -> Dict:
    return {
        "host": dest["host"],
        "user": dest["user"],
        "port": dest["port"],
        "use_sudo": dest["use_sudo"],
        "ssh_key_configured": bool(dest.get("ssh_key")),
    }


def remote_docker(use_sudo: bool) -> str:
    if use_sudo:
        return 'sudo -n docker'
    return 'docker'


def remote_load_command(compress: bool, use_sudo: bool) -> str:
    docker = remote_docker(use_sudo)
    if compress:
        return f'gzip -dc | {docker} load'
    return f'{docker} load'


def remote_inspect_command(image: str, use_sudo: bool) -> str:
    validate_image_ref(image)
    docker = remote_docker(use_sudo)
    return f"{docker} image inspect --format '{{{{.Id}}}}' {shlex.quote(image)}"


def build_ssh_command(dest: Dict, remote_command: str) -> List[str]:
    command = [
        'ssh',
        '-p', str(dest['port']),
        '-o', 'BatchMode=yes',
        '-o', 'ConnectTimeout=20',
        '-o', 'ServerAliveInterval=30',
        '-o', 'StrictHostKeyChecking=accept-new',
    ]
    if dest.get('ssh_key'):
        command.extend(['-i', dest['ssh_key'], '-o', 'IdentitiesOnly=yes'])
    command.append(f"{dest['user']}@{dest['host']}")
    command.append(remote_command)
    return command


def parse_image_inspect_lines(stdout: str) -> List[Dict]:
    images = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split('|', 2)
        if len(parts) != 3:
            continue
        image_id, size_text, tags_json = parts
        try:
            size = int(size_text.strip())
            raw_tags = json.loads(tags_json.strip())
        except (TypeError, ValueError, json.JSONDecodeError):
            continue
        tags = []
        if isinstance(raw_tags, list):
            tags = [tag for tag in raw_tags if isinstance(tag, str)]
        images.append({
            "id": image_id.strip(),
            "tags": tags,
            "size_bytes": size,
            "size": format_bytes(size),
        })
    images.sort(key=lambda item: item["size_bytes"], reverse=True)
    return images


def memory_note(containers: List[Dict], stopped: List[Dict], removed_images: List[str]) -> str:
    running = [item for item in containers if item.get("state") == "running"]
    if removed_images and stopped:
        return (
            "Stopped the containers and removed the local image layers. RAM from those "
            "containers and disk from those layers are released. Volumes were left in place."
        )
    if removed_images:
        return (
            "Removed the local image layers after copying them. Disk used by those "
            "layers is released. RAM drops when containers that were using them are stopped."
        )
    if stopped:
        return (
            "Stopped containers that used these images, which releases their RAM. "
            "The image layers still use disk until they are removed and no container references them."
        )
    if running:
        return (
            "Copied the images. Containers using them are still running, so RAM use "
            "on this machine is unchanged. Stop those containers after the other aaPanel is serving them."
        )
    return (
        "Copied the images. No running container was using them, so RAM is unchanged. "
        "Disk is unchanged until the local images are removed."
    )


def _summarize_container(container: Dict) -> Dict:
    return {
        "id": container.get("ID"),
        "name": container.get("Names"),
        "image": container.get("Image"),
        "state": container.get("State"),
    }


class DockerImageService:
    def list_images(self) -> Dict:
        try:
            return self._list_images()
        except DockerImageError as exc:
            return {"error": str(exc)}
        except subprocess.TimeoutExpired:
            return {"error": "timed out while reading Docker image usage"}
        except FileNotFoundError as exc:
            return {"error": f"Required command not found: {exc.filename}"}
        except Exception as exc:
            return {"error": str(exc)}

    def transfer(self, params: Dict, targets: Optional[Dict] = None) -> Dict:
        try:
            return self._transfer(params, targets or {})
        except DockerImageError as exc:
            return {"error": str(exc)}
        except subprocess.TimeoutExpired:
            return {"error": "Docker image transfer timed out"}
        except FileNotFoundError as exc:
            return {"error": f"Required command not found: {exc.filename}"}
        except Exception as exc:
            return {"error": str(exc)}

    def _run(self, command: List[str], timeout: int) -> subprocess.CompletedProcess:
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def _snapshot(self) -> Dict:
        memory = self._run(['free', '-h'], 5)
        disk = self._run(['docker', 'system', 'df'], 30)
        return {
            "memory": _clip(memory.stdout if memory.returncode == 0 else memory.stderr),
            "disk": _clip(disk.stdout if disk.returncode == 0 else disk.stderr),
        }

    def _list_images(self) -> Dict:
        listed = self._run(['docker', 'images', '-q'], 30)
        if listed.returncode != 0:
            raise DockerImageError(_clip(listed.stderr) or "failed to list Docker images")
        ids = []
        for line in listed.stdout.splitlines():
            image_id = line.strip()
            if IMAGE_ID_RE.fullmatch(image_id) and image_id not in ids:
                ids.append(image_id)
        images = []
        inspect_format = '{{.Id}}|{{.Size}}|{{json .RepoTags}}'
        for batch in _batches(ids, INSPECT_BATCH):
            inspected = self._run(
                ['docker', 'image', 'inspect', '--format', inspect_format, *batch],
                60,
            )
            if inspected.returncode != 0:
                raise DockerImageError(_clip(inspected.stderr) or "failed to inspect Docker images")
            images.extend(parse_image_inspect_lines(inspected.stdout))
        images.sort(key=lambda item: item["size_bytes"], reverse=True)
        stats = self._run(
            ['docker', 'stats', '--no-stream', '--format', '{{json .}}'],
            30,
        )
        containers = []
        if stats.returncode == 0:
            for line in stats.stdout.splitlines():
                if not line.strip():
                    continue
                try:
                    containers.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        snapshot = self._snapshot()
        return {
            "images": images,
            "count": len(images),
            "running_containers": containers,
            "memory": snapshot["memory"],
            "disk": snapshot["disk"],
        }

    def _inspect_local(self, image: str) -> Dict:
        result = self._run(
            [
                'docker', 'image', 'inspect',
                '--format', '{"id":"{{.Id}}","size":{{.Size}}}',
                image,
            ],
            30,
        )
        if result.returncode != 0 or not result.stdout.strip():
            detail = _clip(result.stderr).strip()
            message = f"image not found locally: {image}"
            if detail:
                message = f"{message} ({detail})"
            raise DockerImageError(message)
        try:
            data = json.loads(result.stdout.strip().splitlines()[0])
        except json.JSONDecodeError as exc:
            raise DockerImageError(f"could not read local image metadata for {image}") from exc
        size = int(data.get("size") or 0)
        return {"name": image, "id": data.get("id"), "size_bytes": size, "size": format_bytes(size)}

    def _containers_for(self, image: str) -> List[Dict]:
        result = self._run(
            ['docker', 'ps', '-a', '--filter', f'ancestor={image}', '--format', '{{json .}}'],
            30,
        )
        if result.returncode != 0:
            raise DockerImageError(
                f"could not list containers for {image}: {_clip(result.stderr)}"
            )
        found = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                found.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise DockerImageError(f"could not parse containers for {image}") from exc
        return found

    def _collect_containers(self, images: List[str]) -> List[Dict]:
        by_id = {}
        for image in images:
            for container in self._containers_for(image):
                container_id = container.get("ID")
                if container_id:
                    by_id[container_id] = container
        return list(by_id.values())

    def _transfer(self, params: Dict, targets: Dict) -> Dict:
        if not isinstance(params, dict):
            raise DockerImageError("params must be an object")
        images = normalize_images(params.get('images'))
        dest = resolve_destination(params, targets)
        compress = _flag(params.get('compress'), True)
        dry_run = _flag(params.get('dry_run'), False)
        stop_containers = _flag(params.get('stop_containers'), False)
        remove_containers = _flag(params.get('remove_containers'), False)
        remove_local = _flag(params.get('remove_local'), False)
        timeout = _timeout_seconds(params.get('timeout_seconds'))

        local_images = [self._inspect_local(image) for image in images]
        containers = [_summarize_container(item) for item in self._collect_containers(images)]
        before = self._snapshot()
        plan = {
            "images": local_images,
            "containers": containers,
            "destination": public_destination(dest),
            "compress": compress,
            "stop_containers": stop_containers,
            "remove_containers": remove_containers,
            "remove_local": remove_local,
            "not_transferred": list(NOT_TRANSFERRED),
            "disk_before": before["disk"],
            "memory_before": before["memory"],
        }
        if dry_run:
            plan.update({
                "success": True,
                "dry_run": True,
                "memory_note": (
                    "Dry run only. Nothing was copied. Image layers use disk; "
                    "running containers use RAM."
                ),
            })
            return plan

        streamed = self._stream_images(images, dest, compress, timeout)
        if not streamed["ok"]:
            return {
                **plan,
                "success": False,
                "error": streamed.get("error") or "image transfer failed",
                "output": streamed.get("stdout", ""),
                "stderr": streamed.get("stderr", ""),
            }

        verified = []
        for image in images:
            check = self._run(
                build_ssh_command(dest, remote_inspect_command(image, dest["use_sudo"])),
                120,
            )
            image_id = check.stdout.strip()
            if check.returncode != 0 or not image_id:
                return {
                    **plan,
                    "success": False,
                    "error": f"destination did not load {image}",
                    "output": _clip(check.stdout),
                    "stderr": _clip(check.stderr),
                    "verified": verified,
                }
            verified.append({"name": image, "id": image_id})

        stopped, removed_containers, removed_images, cleanup_errors = self._cleanup(
            containers,
            images,
            stop_containers,
            remove_containers,
            remove_local,
        )
        after = self._snapshot()
        result = {
            **plan,
            "success": not cleanup_errors,
            "transferred": True,
            "verified": verified,
            "containers_stopped": stopped,
            "containers_removed": removed_containers,
            "images_removed_locally": removed_images,
            "cleanup_errors": cleanup_errors,
            "output": streamed.get("stdout", ""),
            "disk_after": after["disk"],
            "memory_after": after["memory"],
            "memory_note": memory_note(containers, stopped, removed_images),
        }
        if cleanup_errors:
            result["error"] = cleanup_errors[0]
        return result

    def _cleanup(self, containers, images, stop_containers, remove_containers, remove_local):
        stopped = []
        removed_containers = []
        removed_images = []
        cleanup_errors = []
        state_by_id = {}
        usable = []
        for container in containers:
            container_id = container.get("id")
            if not isinstance(container_id, str) or not CONTAINER_ID_RE.fullmatch(container_id):
                cleanup_errors.append("skipped a container with an unexpected id")
                continue
            usable.append(container)
            state_by_id[container_id] = container.get("state")

        if stop_containers:
            for container in usable:
                if container.get("state") != "running":
                    continue
                result = self._run(['docker', 'stop', container["id"]], 180)
                if result.returncode == 0:
                    stopped.append({"id": container["id"], "name": container.get("name")})
                    state_by_id[container["id"]] = "exited"
                else:
                    cleanup_errors.append(
                        f"failed to stop {container.get('name') or container['id']}: {_clip(result.stderr)}"
                    )

        if remove_containers:
            for container in usable:
                if state_by_id.get(container["id"]) == "running":
                    cleanup_errors.append(
                        f"{container.get('name') or container['id']} is still running"
                    )
                    continue
                result = self._run(['docker', 'rm', container["id"]], 60)
                if result.returncode == 0:
                    removed_containers.append({"id": container["id"], "name": container.get("name")})
                else:
                    cleanup_errors.append(
                        f"failed to remove {container.get('name') or container['id']}: {_clip(result.stderr)}"
                    )

        if remove_local:
            for image in images:
                result = self._run(['docker', 'rmi', image], 180)
                if result.returncode == 0:
                    removed_images.append(image)
                else:
                    cleanup_errors.append(f"failed to remove local image {image}: {_clip(result.stderr)}")

        return stopped, removed_containers, removed_images, cleanup_errors

    def _stream_images(self, images: List[str], dest: Dict, compress: bool, timeout: int) -> Dict:
        save = subprocess.Popen(
            ['docker', 'save', *images],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        compressor = None
        ssh = None
        source = save
        try:
            if compress:
                compressor = subprocess.Popen(
                    ['gzip', '-1c'],
                    stdin=save.stdout,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                save.stdout.close()
                source = compressor
            ssh = subprocess.Popen(
                build_ssh_command(dest, remote_load_command(compress, dest["use_sudo"])),
                stdin=source.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            source.stdout.close()
        except Exception:
            _terminate(ssh)
            _terminate(compressor)
            _terminate(save)
            raise

        save_err, comp_err, ssh_out, ssh_err = [], [], [], []
        threads = [
            _reader(save.stderr, save_err),
            _reader(ssh.stdout, ssh_out),
            _reader(ssh.stderr, ssh_err),
        ]
        if compressor is not None:
            threads.append(_reader(compressor.stderr, comp_err))
        for thread in threads:
            thread.start()

        timed_out = False
        try:
            ssh.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True

        ssh_failed = ssh.returncode not in (0, None)
        save_failed = save.poll() is not None and save.returncode not in (0, None)
        if timed_out or ssh_failed:
            # Stopping a still-running save must not be reported as a save failure.
            _terminate(ssh)
            _terminate(compressor)
            _terminate(save)
        else:
            _wait_or_kill(compressor, 60)
            _wait_or_kill(save, 60)
            save_failed = save.returncode not in (0, None)
        for thread in threads:
            thread.join(timeout=30)

        stdout = _clip(_decode(ssh_out))
        stderr = _clip("\n".join(part for part in (
            _decode(save_err),
            _decode(comp_err),
            _decode(ssh_err),
        ) if part))
        if timed_out:
            return {
                "ok": False,
                "error": f"transfer timed out after {timeout} seconds",
                "stdout": stdout,
                "stderr": stderr,
            }
        if save_failed:
            return {
                "ok": False,
                "error": "docker save failed",
                "stdout": stdout,
                "stderr": stderr,
            }
        if ssh_failed:
            return {
                "ok": False,
                "error": "remote docker load failed",
                "stdout": stdout,
                "stderr": stderr,
            }
        return {"ok": True, "stdout": stdout, "stderr": stderr}


def _batches(items: List[str], size: int):
    for index in range(0, len(items), size):
        yield items[index:index + size]


def _decode(chunks: List[bytes]) -> str:
    return b''.join(chunks).decode('utf-8', errors='replace').strip()


def _reader(pipe, bucket: List[bytes]) -> threading.Thread:
    def _read():
        try:
            bucket.append(pipe.read() or b'')
        except Exception:
            bucket.append(b'')

    thread = threading.Thread(target=_read)
    thread.daemon = True
    return thread


def _terminate(proc) -> None:
    if proc is None or proc.poll() is not None:
        return
    proc.kill()
    try:
        proc.wait(timeout=10)
    except Exception:
        return


def _wait_or_kill(proc, timeout: int) -> None:
    if proc is None:
        return
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        _terminate(proc)
