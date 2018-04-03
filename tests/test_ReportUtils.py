"""Unit tests for ReportUtils"""

import unittest
import os

import toml
from elasticsearch import Elasticsearch, exceptions

import gracc_reporting.ReportUtils as ReportUtils

CONFIG_FILE = 'test_config.toml'
BAD_CONFIG_FILE = 'test_bad_config.toml'


class FakeVOReport(ReportUtils.Reporter):
    """Fake Report class on top of ReportUtils.Reporter"""
    def __init__(self, cfg_file=CONFIG_FILE, vo=None, althost_key=None):
        report = 'test'
        start = '2018-03-28 06:30'
        end = '2018-03-29 06:30'
        super(FakeVOReport, self).__init__(report=report, config=cfg_file,
                                         start=start, end=end, vo=vo, 
                                         althost_key=althost_key)

    # Defined to satisfy abstract class constraints
    def query(self): pass
    def run_report(self): pass


class TestReportUtilsBase(unittest.TestCase):
    """Base class for ReportUtils tests"""
    def setUp(self):
        self.r = FakeVOReport(vo='testVO')
        self.r_copy = FakeVOReport(cfg_file=BAD_CONFIG_FILE)


class TestGetLogfilePath(TestReportUtilsBase):
    """Tests for ReportUtils.Reporter.get_logfile_path"""
    def test_override(self):
        """Return override logfile if that's passed in"""
        fn = "/tmp/override.log"
        self.assertEqual(self.r.get_logfile_path(fn), fn)

    def test_configfile(self):
        """Logfile should be set to configfile value"""
        answer = os.path.join(self.r.config["default_logdir"], 'gracc-reporting',
            'test.log')
        self.assertEqual(self.r.get_logfile_path(), answer)

    def test_fallback(self):
        """Set logdir to $HOME if no override and no configfile value"""
        answer = os.path.join(os.path.expanduser('~'), 'gracc-reporting', 
            'test.log')
        self.assertEqual(self.r_copy.get_logfile_path(), answer)

    def test_bad_configval(self):
        """Set logdir to $HOME if configfile value is invalid"""
        self.r_copy.config["default_logdir"] = '/'
        answer = os.path.join(os.path.expanduser('~'), 'gracc-reporting',
                              'test.log')
        self.assertEqual(self.r_copy.get_logfile_path(), answer)
        del self.r_copy.config["default_logdir"]


class TestParseConfig(TestReportUtilsBase):
    """Tests for ReportUtils.Reporter._parse_config"""
    def test_parse_config_control(self):
        """Parse a normal config"""
        answer = {u'test': {
                    u'index_pattern': u'gracc.osg.raw-%Y.%m', 
                    u'to_emails': [u'nobody@example.com'],
                    u'to_names' : [u'test name'],
                    u'testvo': {
                        u'min_hours': 1000, 
                        u'min_efficiency': 0.5, 
                        u'to_emails': [u'nobody@example.com']
                        }
                    }, 
                    u'configured_vos': [u'testvo'], 
                    u'elasticsearch': {
                        u'hostname': u'https://gracc.opensciencegrid.org/q',
                        u'secondary_host': u'https://gracc.opensciencegrid.org/q',
                        u'bad_host': u'https://www.blah.badurl'
                        }, 
                    u'email': {
                        u'test': {
                            u'names': [u'Test Recipient'], 
                            u'emails': [u'nobody@example.com']
                            }, 
                        u'from': {
                            u'name': u'GRACC Operations', 
                            u'email': u'nobody@example.com'
                        }, 
                        u'smtphost': u'smtp.example.com'
                    }, 
                    u'default_logdir': u'/tmp/gracc-test'
                }
        self.assertDictEqual(self.r._parse_config(CONFIG_FILE), answer)

    def test_invalid_config(self):
        """Raise toml.TomlDecodeError if we're parsing a bad config file"""
        bad_toml = "blahblah\""
        junk_file = "/tmp/junk.toml"

        with open(junk_file, 'w') as f:
            f.write(bad_toml)

        self.assertRaises(toml.TomlDecodeError, self.r._parse_config, junk_file)


class TestCheckVO(unittest.TestCase):
    """We're not going to actually test ReportUtils.Reporter.__check_vo 
    directly. We're instead going to check for behavior if we pass a valid 
    and invalid VO into the class instantiation"""

    def test_valid_vo(self):
        """Instantiate Reporter with a valid VO"""
        answer = "testVO"
        good_report_inst = FakeVOReport(vo=answer)
        self.assertEqual(good_report_inst.vo, answer)
        del good_report_inst

    def test_bad_vo(self):
        """Instantiate Reporter with an invalid VO"""
        self.assertRaises(KeyError, FakeVOReport, vo="thisshouldfail")
        

class TestEstablishClient(unittest.TestCase):
    """Test establishing of Elasticsearch client"""
    def test_default_case(self):
        """Automatically pass because all other tests 
        must pass this to run""" 
        pass

    def test_no_althostkey_no_config_entry(self):
        """host should return https://gracc.opensciencegrid.org/q if no
        althost is specified and there is no config file entry"""
        _cfg = BAD_CONFIG_FILE 
        test_report = FakeVOReport(cfg_file=_cfg)
        self.assertEqual(test_report.client.transport.hosts[0]['host'], 
                         'gracc.opensciencegrid.org')
        del test_report

    def test_althost_key(self):
        """Connect to host specified in secondary_host key"""
        test_report_ok = FakeVOReport(althost_key='secondary_host')
        self.assertEqual(test_report_ok.client.transport.hosts[0]['host'], 
                         'gracc.opensciencegrid.org')
        del test_report_ok

    def test_althost_bad(self):
        """Raise SystemExit if connecting to a bad host"""
        # test_report_bad = FakeVOReport(althost_key='bad_host')
        self.assertRaises(SystemExit, FakeVOReport, althost_key='bad_host')
