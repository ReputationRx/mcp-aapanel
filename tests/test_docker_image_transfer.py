import importlib.util
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import docker_images
from docker_images import (
    DockerImageError,
    DockerImageService,
    build_ssh_command,
    format_bytes,
    memory_note,
    normalize_images,
    parse_image_inspect_lines,
    remote_inspect_command,
    remote_load_command,
    resolve_destination,
)


class FakePopen:
    calls = []
    hang_ssh = False
    ssh_returncode = 0
    save_returncode = 0

    def __init__(self, cmd, stdin=None, stdout=None, stderr=None):
        self.cmd = list(cmd)
        FakePopen.calls.append(self.cmd)
        self.returncode = 0
        if cmd[0] == 'ssh':
            self.returncode = FakePopen.ssh_returncode
        if cmd[0] == 'docker':
            self.returncode = FakePopen.save_returncode
        self.stdout = io.BytesIO(b'Loaded image: nginx:1.27\n') if stdout == subprocess.PIPE else None
        self.stderr = io.BytesIO(b'') if stderr == subprocess.PIPE else None
        self._killed = False

    def wait(self, timeout=None):
        if self.cmd and self.cmd[0] == 'ssh' and FakePopen.hang_ssh:
            raise subprocess.TimeoutExpired(self.cmd, timeout)
        if self._killed:
            self.returncode = -9
        return self.returncode

    def poll(self):
        if self._killed:
            return -9
        if self.cmd and self.cmd[0] == 'ssh' and FakePopen.hang_ssh:
            return None
        return self.returncode

    def kill(self):
        self._killed = True
        self.returncode = -9


class Runner:
    def __init__(self):
        self.calls = []
        self.fail_remote = False

    def __call__(self, cmd, timeout=None, **kwargs):
        command = list(cmd)
        self.calls.append(command)
        text = kwargs.get('text', True)

        def done(code, out='', err=''):
            if not text:
                out = out.encode()
                err = err.encode()
            return subprocess.CompletedProcess(command, code, out, err)

        if command[0] == 'free':
            return done(0, 'Mem: 16Gi 10Gi 5Gi\n')
        if command[:3] == ['docker', 'system', 'df']:
            return done(0, 'Images  2  1GB\n')
        if command[:2] == ['docker', 'images']:
            return done(0, 'abc123def456\n')
        if command[:4] == ['docker', 'image', 'inspect', '--format'] and '{{json .RepoTags}}' in command[4]:
            return done(0, 'sha256:abc|2097152|["nginx:1.27"]\nsha256:def|1024|["redis:7"]\n')
        if command[:3] == ['docker', 'image', 'inspect']:
            image = command[-1]
            if image == 'missing:latest':
                return done(1, '', 'No such image')
            return done(0, '{"id":"sha256:abc","size":1048576}\n')
        if command[:2] == ['docker', 'ps']:
            return done(0, '{"ID":"abc123def456","Names":"web","Image":"nginx:1.27","State":"running"}\n')
        if command[:2] == ['docker', 'stats']:
            return done(0, '{"Name":"web","MemUsage":"512MiB / 16GiB"}\n')
        if command[0] == 'ssh':
            if self.fail_remote:
                return done(1, '', 'No such image')
            return done(0, 'sha256:abc\n')
        if command[:2] == ['docker', 'stop']:
            return done(0, command[-1] + '\n')
        if command[:2] == ['docker', 'rm']:
            return done(0, command[-1] + '\n')
        if command[:2] == ['docker', 'rmi']:
            return done(0, 'Untagged: ' + command[-1] + '\n')
        return done(1, '', 'unexpected command')


def service_with(runner):
    service = DockerImageService()
    service._run = runner
    return service


class DockerImageHelperTests(unittest.TestCase):
    def test_format_bytes(self):
        self.assertEqual(format_bytes(0), '0 B')
        self.assertEqual(format_bytes(1536), '1.5 KB')
        self.assertEqual(format_bytes(1024 ** 3), '1.0 GB')

    def test_rejects_shell_metacharacters(self):
        with self.assertRaises(DockerImageError):
            normalize_images(['nginx;rm -rf /'])
        with self.assertRaises(DockerImageError):
            normalize_images(['nginx:latest', 'redis && true'])

    def test_dedupes_and_accepts_a_single_string(self):
        self.assertEqual(normalize_images('nginx:1.27'), ['nginx:1.27'])
        self.assertEqual(
            normalize_images(['nginx:1.27', 'nginx:1.27', 'redis:7']),
            ['nginx:1.27', 'redis:7'],
        )

    def test_rejects_bad_destination(self):
        with self.assertRaises(DockerImageError):
            resolve_destination({'host': 'evil.com;id', 'images': ['nginx']}, {})
        with self.assertRaises(DockerImageError):
            resolve_destination({'host': '203.0.113.10', 'user': 'root;id'}, {})
        with self.assertRaises(DockerImageError):
            resolve_destination({'target': 'nope', 'images': ['nginx']}, {})

    def test_target_host_can_be_overridden(self):
        with tempfile.NamedTemporaryFile() as key:
            dest = resolve_destination(
                {'target': 'secondary', 'host': '198.51.100.8'},
                {'secondary': {'host': '203.0.113.10', 'user': 'root', 'ssh_key': key.name}},
            )
        self.assertEqual(dest['host'], '198.51.100.8')
        self.assertEqual(dest['user'], 'root')
        self.assertTrue(dest['ssh_key'])

    def test_remote_commands_are_quoted(self):
        self.assertEqual(
            remote_load_command(True, False),
            'gzip -dc | docker load',
        )
        self.assertEqual(
            remote_load_command(False, True),
            'sudo -n docker load',
        )
        self.assertEqual(
            remote_inspect_command('nginx:1.27', False),
            "docker image inspect --format '{{.Id}}' nginx:1.27",
        )
        command = build_ssh_command(
            {
                'host': '203.0.113.10',
                'user': 'root',
                'port': 22,
                'ssh_key': '/root/.ssh/id_ed25519',
                'use_sudo': False,
            },
            remote_load_command(True, False),
        )
        self.assertEqual(command[0], 'ssh')
        self.assertEqual(command[-1], 'gzip -dc | docker load')
        self.assertIn('root@203.0.113.10', command)
        self.assertNotIn(';', command[-1])

    def test_parse_and_sort_images_by_size(self):
        images = parse_image_inspect_lines(
            'sha256:small|100|["tiny:1"]\nsha256:big|5000|["big:1"]\n'
        )
        self.assertEqual([item['id'] for item in images], ['sha256:big', 'sha256:small'])
        self.assertEqual(images[0]['tags'], ['big:1'])

    def test_memory_note_distinguishes_ram_and_disk(self):
        running = [{'state': 'running'}]
        note = memory_note(running, [], [])
        self.assertIn('RAM use', note)
        self.assertIn('still running', note)


class DockerImageTransferTests(unittest.TestCase):
    def setUp(self):
        FakePopen.calls = []
        FakePopen.hang_ssh = False
        FakePopen.ssh_returncode = 0
        FakePopen.save_returncode = 0
        self.runner = Runner()

    def test_list_images_sorts_and_includes_usage(self):
        result = service_with(self.runner).list_images()
        self.assertEqual(result['count'], 2)
        self.assertEqual(result['images'][0]['tags'], ['nginx:1.27'])
        self.assertGreater(result['images'][0]['size_bytes'], result['images'][1]['size_bytes'])
        self.assertEqual(result['running_containers'][0]['Name'], 'web')
        self.assertIn('Mem:', result['memory'])

    def test_dry_run_does_not_open_ssh(self):
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {'images': ['nginx:1.27'], 'host': '203.0.113.10', 'dry_run': True},
                {},
            )
        self.assertTrue(result['success'])
        self.assertTrue(result['dry_run'])
        self.assertEqual(result['containers'][0]['name'], 'web')
        self.assertEqual(FakePopen.calls, [])
        self.assertFalse(any(call[0] == 'ssh' for call in self.runner.calls))
        self.assertEqual(result['not_transferred'][0], 'container configuration')

    def test_transfer_streams_save_into_remote_load(self):
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {'images': ['nginx:1.27', 'nginx:1.27'], 'host': '203.0.113.10'},
                {},
            )
        self.assertTrue(result['success'])
        self.assertEqual(result['verified'][0]['name'], 'nginx:1.27')
        save = FakePopen.calls[0]
        ssh = FakePopen.calls[-1]
        self.assertEqual(save[:2], ['docker', 'save'])
        self.assertEqual(save[2:], ['nginx:1.27'])
        self.assertEqual(ssh[-1], 'gzip -dc | docker load')
        self.assertFalse(any(call[:2] == ['docker', 'rmi'] for call in self.runner.calls))
        self.assertFalse(any(call[:2] == ['docker', 'stop'] for call in self.runner.calls))
        self.assertIn('still running', result['memory_note'])

    def test_uncompressed_sudo_load_command(self):
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {
                    'images': 'redis:7',
                    'host': '203.0.113.10',
                    'compress': False,
                    'use_sudo': True,
                },
                {},
            )
        self.assertTrue(result['success'])
        self.assertEqual(FakePopen.calls[-1][-1], 'sudo -n docker load')
        self.assertTrue(all(call[0] != 'gzip' for call in FakePopen.calls))

    def test_cleanup_runs_only_after_destination_has_the_image(self):
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {
                    'images': ['nginx:1.27'],
                    'target': 'secondary',
                    'stop_containers': True,
                    'remove_containers': True,
                    'remove_local': True,
                },
                {'secondary': {'host': '203.0.113.10', 'user': 'panel'}},
            )
        self.assertTrue(result['success'])
        self.assertEqual(result['destination']['user'], 'panel')
        self.assertEqual(result['containers_stopped'][0]['id'], 'abc123def456')
        self.assertEqual(result['containers_removed'][0]['id'], 'abc123def456')
        self.assertEqual(result['images_removed_locally'], ['nginx:1.27'])
        commands = [call[:2] for call in self.runner.calls]
        self.assertLess(commands.index(['ssh', '-p']), commands.index(['docker', 'rmi']))

    def test_failed_load_does_not_remove_local_images(self):
        FakePopen.ssh_returncode = 255
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {
                    'images': ['nginx:1.27'],
                    'host': '203.0.113.10',
                    'remove_local': True,
                    'stop_containers': True,
                },
                {},
            )
        self.assertFalse(result['success'])
        self.assertIn('remote docker load failed', result['error'])
        self.assertFalse(any(call[:2] == ['docker', 'rmi'] for call in self.runner.calls))
        self.assertFalse(any(call[:2] == ['docker', 'stop'] for call in self.runner.calls))

    def test_failed_verification_does_not_remove_local_images(self):
        self.runner.fail_remote = True
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {'images': ['nginx:1.27'], 'host': '203.0.113.10', 'remove_local': True},
                {},
            )
        self.assertFalse(result['success'])
        self.assertIn('destination did not load', result['error'])
        self.assertFalse(any(call[:2] == ['docker', 'rmi'] for call in self.runner.calls))

    def test_timeout_does_not_remove_local_images(self):
        FakePopen.hang_ssh = True
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {'images': ['nginx:1.27'], 'host': '203.0.113.10', 'remove_local': True},
                {},
            )
        self.assertFalse(result['success'])
        self.assertIn('timed out', result['error'])
        self.assertFalse(any(call[:2] == ['docker', 'rmi'] for call in self.runner.calls))

    def test_missing_image_is_rejected_before_ssh(self):
        with mock.patch('docker_images.subprocess.Popen', FakePopen):
            result = service_with(self.runner).transfer(
                {'images': ['missing:latest'], 'host': '203.0.113.10'},
                {},
            )
        self.assertIn('image not found locally', result['error'])
        self.assertEqual(FakePopen.calls, [])


def load_server_module():
    path = Path(__file__).resolve().parents[1] / 'aapanel-mcp-server.py'
    spec = importlib.util.spec_from_file_location('aapanel_mcp_server', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ServerRoutingTests(unittest.TestCase):
    def test_methods_delegate_to_the_image_service(self):
        module = load_server_module()
        server = module.AAPanelMCPServer()
        calls = []

        class FakeService:
            def list_images(self):
                calls.append('list')
                return {'images': []}

            def transfer(self, params, targets):
                calls.append((params, targets))
                return {'success': True}

        server.image_service = FakeService()
        server.docker_targets = {'secondary': {'host': '203.0.113.10'}}
        listed = server.handle_request({'method': 'aapanel/list_docker_images'})
        transferred = server.handle_request({
            'method': 'aapanel/transfer_docker_images',
            'params': {'images': ['nginx:1.27'], 'target': 'secondary'},
        })
        self.assertEqual(listed, {'images': []})
        self.assertEqual(calls[0], 'list')
        self.assertTrue(transferred['success'])
        self.assertEqual(calls[1][1]['secondary']['host'], '203.0.113.10')


if __name__ == '__main__':
    unittest.main()
