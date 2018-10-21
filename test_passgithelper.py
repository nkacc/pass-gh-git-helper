import io
import logging

import pytest

import passgithelper


@pytest.fixture
def xdg_dir(request, mocker):
    xdg_mock = mocker.patch('xdg.BaseDirectory.load_first_config')
    xdg_mock.return_value = request.param


def test_handle_skip_nothing(monkeypatch):
    monkeypatch.delenv('PASS_GIT_HELPER_SKIP', raising=False)
    passgithelper.handle_skip()
    # should do nothing normally


def test_handle_skip_exits(monkeypatch):
    monkeypatch.setenv('PASS_GIT_HELPER_SKIP', '1')
    with pytest.raises(SystemExit):
        passgithelper.handle_skip()


@pytest.mark.parametrize(
    'xdg_dir',
    [None],
    indirect=True,
)
def test_parse_mapping_file_missing(xdg_dir):
    with pytest.raises(RuntimeError):
        passgithelper.parse_mapping(None)


@pytest.mark.parametrize(
    'xdg_dir',
    ['test_data/smoke'],
    indirect=True,
)
def test_parse_mapping_from_xdg(xdg_dir):
    config = passgithelper.parse_mapping(None)
    assert 'mytest.com' in config
    assert config['mytest.com']['target'] == 'dev/mytest'


class TestScript:

    def test_help(self, capsys):
        with pytest.raises(SystemExit):
            passgithelper.main(['--help'])

        assert 'usage: ' in capsys.readouterr().out

    def test_skip(self, monkeypatch, capsys):
        monkeypatch.setenv('PASS_GIT_HELPER_SKIP', '1')
        with pytest.raises(SystemExit):
            passgithelper.main(['get'])
        out, err = capsys.readouterr()
        assert not out
        assert not err

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/smoke'],
        indirect=True,
    )
    def test_smoke_resolve(self, xdg_dir, monkeypatch, mocker, capsys):
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=mytest.com'''))
        subprocess_mock = mocker.patch('subprocess.check_output')
        subprocess_mock.return_value = b'narf'

        passgithelper.main(['get'])

        subprocess_mock.assert_called_once()
        subprocess_mock.assert_called_with(['pass', 'show', 'dev/mytest'])

        out, _ = capsys.readouterr()
        assert out == 'password=narf\n'

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/smoke'],
        indirect=True,
    )
    def test_path_used_if_present_fails(self, xdg_dir, monkeypatch, caplog):
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=mytest.com
path=/foo/bar.git'''))

        with pytest.raises(SystemExit):
            passgithelper.main(['get'])
        assert caplog.record_tuples == [
            ('root', logging.WARN, 'No mapping matched'),
        ]

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/with-path'],
        indirect=True,
    )
    def test_path_used_if_present(self, xdg_dir, monkeypatch, mocker, capsys):
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=mytest.com
path=subpath/bar.git'''))

        subprocess_mock = mocker.patch('subprocess.check_output')
        subprocess_mock.return_value = b'narf'

        passgithelper.main(['get'])

        subprocess_mock.assert_called_once()
        subprocess_mock.assert_called_with(['pass', 'show', 'dev/mytest'])

        out, _ = capsys.readouterr()
        assert out == 'password=narf\n'

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/wildcard'],
        indirect=True,
    )
    def test_wildcard_matching(self, xdg_dir, monkeypatch, mocker, capsys):
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=wildcard.com
path=subpath/bar.git'''))

        subprocess_mock = mocker.patch('subprocess.check_output')
        subprocess_mock.return_value = b'narf-wildcard'

        passgithelper.main(['get'])

        subprocess_mock.assert_called_once()
        subprocess_mock.assert_called_with(
            ['pass', 'show', 'dev/wildcard.com'])

        out, _ = capsys.readouterr()
        assert out == 'password=narf-wildcard\n'

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/with-username'],
        indirect=True,
    )
    def test_username_provided(self, xdg_dir, monkeypatch, mocker, capsys):
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=plainline.com'''))

        subprocess_mock = mocker.patch('subprocess.check_output')
        subprocess_mock.return_value = b'password\nusername'

        passgithelper.main(['get'])

        subprocess_mock.assert_called_once()
        subprocess_mock.assert_called_with(
            ['pass', 'show', 'dev/plainline'])

        out, _ = capsys.readouterr()
        assert out == 'password=password\nusername=username\n'

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/with-username'],
        indirect=True,
    )
    def test_username_skipped_if_provided(
            self, xdg_dir, monkeypatch, mocker, capsys):
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=plainline.com
username=narf'''))

        subprocess_mock = mocker.patch('subprocess.check_output')
        subprocess_mock.return_value = b'password\nusername'

        passgithelper.main(['get'])

        subprocess_mock.assert_called_once()
        subprocess_mock.assert_called_with(
            ['pass', 'show', 'dev/plainline'])

        out, _ = capsys.readouterr()
        assert out == 'password=password\n'

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/with-username'],
        indirect=True,
    )
    def test_custom_mapping_used(self, xdg_dir, monkeypatch, mocker, capsys):
        # this would fail for the default file from with-username
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=mytest.com'''))
        subprocess_mock = mocker.patch('subprocess.check_output')
        subprocess_mock.return_value = b'narf'

        passgithelper.main(
            ['-m', 'test_data/smoke/git-pass-mapping.ini', 'get'])

        subprocess_mock.assert_called_once()
        subprocess_mock.assert_called_with(['pass', 'show', 'dev/mytest'])

        out, _ = capsys.readouterr()
        assert out == 'password=narf\n'

    @pytest.mark.parametrize(
        'xdg_dir',
        ['test_data/with-username-skip'],
        indirect=True,
    )
    def test_prefix_skipping(self, xdg_dir, monkeypatch, mocker, capsys):
        monkeypatch.setattr('sys.stdin', io.StringIO('''
protocol=https
host=mytest.com'''))
        subprocess_mock = mocker.patch('subprocess.check_output')
        subprocess_mock.return_value = b'password: xyz\nuser: tester'

        passgithelper.main(['get'])

        subprocess_mock.assert_called_once()
        subprocess_mock.assert_called_with(['pass', 'show', 'dev/mytest'])

        out, _ = capsys.readouterr()
        assert out == 'password=xyz\nusername=tester\n'