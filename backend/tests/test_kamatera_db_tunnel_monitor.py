"""No real SSH, database, process termination or sleep in these regressions."""
import subprocess
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import kamatera_db_tunnel_monitor as monitor


class TunnelMonitorTests(unittest.TestCase):
    def test_missing_state_is_not_considered_healthy(self):
        with patch.object(Path, 'read_text', side_effect=FileNotFoundError):
            self.assertFalse(monitor.ssh_process_running(Path('missing-state.json')))

    def test_unknown_target_is_not_considered_healthy(self):
        with patch.object(Path, 'read_text', return_value='{"Host":"unknown","LocalPort":15432}'):
            self.assertFalse(monitor.ssh_process_running(Path('state.json')))

    def test_malformed_state_is_not_considered_healthy(self):
        with patch.object(Path, 'read_text', return_value='null'):
            self.assertFalse(monitor.ssh_process_running(Path('state.json')))

    def test_healthy_endpoint_is_reused_without_repair(self):
        repair, report = Mock(), Mock()
        monitor.monitor_loop(lambda: True, repair, lambda _: True, report, lambda: False)
        repair.assert_not_called()
        report.assert_called_once_with('ready')

    def test_dropped_endpoint_is_repaired_then_reused(self):
        ready = Mock(side_effect=[False, True, True])
        repair = Mock(return_value=True)
        wait = Mock(side_effect=[False, True])
        states = []
        monitor.monitor_loop(ready, repair, wait, states.append, lambda: False)
        repair.assert_called_once_with()
        self.assertEqual(states, ['reconnecting', 'ready', 'ready'])
        self.assertEqual([call.args[0] for call in wait.call_args_list], [2, 2])

    def test_failed_repairs_back_off_and_never_claim_ready(self):
        waits, states = [], []
        def wait(seconds):
            waits.append(seconds)
            return len(waits) == 6
        monitor.monitor_loop(lambda: False, lambda: False, wait, states.append, lambda: False)
        self.assertEqual(waits, [2, 4, 8, 16, 30, 30])
        self.assertNotIn('ready', states)

    def test_stop_does_not_attempt_a_repair(self):
        repair = Mock()
        monitor.monitor_loop(lambda: False, repair, Mock(), Mock(), lambda: True)
        repair.assert_not_called()

    def test_timeout_is_retried_without_escaping_the_loop(self):
        repair = Mock(side_effect=subprocess.TimeoutExpired('helper', 35))
        states = []
        monitor.monitor_loop(lambda: False, repair, lambda _: True, states.append, lambda: False)
        self.assertEqual(states, ['reconnecting', 'retrying'])

    def test_repair_uses_only_the_existing_one_shot_helper(self):
        script = Path('existing helper.ps1')
        with patch.object(monitor.subprocess, 'run', return_value=Mock(returncode=0)) as run:
            self.assertTrue(monitor.repair_tunnel(script))
        arguments = run.call_args.args[0]
        self.assertEqual(arguments[-3:], ['-File', str(script), '-Once'])
        self.assertEqual(run.call_args.kwargs['timeout'], 35)
        self.assertNotIn('shell', run.call_args.kwargs)


if __name__ == '__main__':
    unittest.main()
