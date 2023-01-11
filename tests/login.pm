# Copyright (C) 2020-2021 SUSE LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

use base 'basetest';
use strict;
use warnings;
use testapi;

sub run {
    assert_screen('login_prompt');
    type_string('root');
    send_key('ret');

    assert_screen('password_prompt');
    type_string('linux');
    send_key('ret');

    # clear the screen so that the textmode_logged_in needle matches
    send_key('ctrl-l');
    assert_screen('textmode_logged_in');

    # run `systemd-analyze blame` with `--no-pager` so that the results are not
    # piped into `less` or `more`
    assert_script_run('systemd-analyze blame --no-pager');

    # perform a sanity check that we got the correct distribution + version
    my $distri = get_var('DISTRI');
    my $version = get_var('VERSION');

    if ($distri eq 'opensuse') {
        # for opensuse we get
        # ID="opensuse-tumbleweed" or ID="opensuse-leap" or ID="opensuse-microos"
        assert_script_run('. /etc/os-release && [[ "${ID}" =~ "opensuse" ]]');

        if ((get_var('HDD_1') =~ /MicroOS/) || (get_var('ISO_1') =~ /MicroOS/)) {
            assert_script_run('. /etc/os-release && [[ "${ID}" =~ "microos" ]]');
        } else {
            assert_script_run('. /etc/os-release && [[ "${ID}" =~ "' . lc($version) . '" ]]');
        }
    } elsif ($distri eq 'fedora') {
        # in Fedora we get:
        # ID=fedora
        # VERSION_ID=34

        # VERSION_ID must be a number:
        assert_script_run('. /etc/os-release && [[ "${VERSION_ID}" =~ ^[0-9]{,4}$ ]]');

        # we don't know the exact version on Rawhide
        if (lc($version) ne 'rawhide') {
            assert_script_run('. /etc/os-release && [[ "${VERSION_ID}" = "' . $version . '" ]]');
        }

        assert_script_run('. /etc/os-release && [[ "${ID}" = "' . $distri . '" ]]', timeout => 1);
    } elsif ($distri eq 'sle') {
        # on SLE:
        # ID="sles"
        # VERSION_ID="15.2"
        assert_script_run('. /etc/os-release && [[ "${VERSION_ID}" =~ "' . $version . '" ]]');
        assert_script_run('. /etc/os-release && [[ "${ID}" = "sles" ]]');
    } elsif (($distri eq 'centos') || ($distri eq 'debian') || ($distri eq 'ubuntu')) {
        # on CentOS:
        # ID="centos"
        # VERSION_ID="7"
        #
        # on Debian:
        # ID=debian
        # VERSION_ID="10"
        #
        # on Ubuntu:
        # ID=ubuntu
        # VERSION_ID="21.04"
        assert_script_run('. /etc/os-release && [[ "${VERSION_ID}" = "' . $version . '" ]]');
        assert_script_run('. /etc/os-release && [[ "${ID}" = "' . $distri . '" ]]');
    } elsif ($distri eq 'archlinux') {
        # on Arch:
        # ID=arch
        # BUILD_ID=rolling
        assert_script_run('. /etc/os-release && [[ "${BUILD_ID}" = "' . $version . '" ]]');
        assert_script_run('. /etc/os-release && [[ "${ID}" = "arch" ]]');
    } else {
        die("No sanity check for $distri-$version is defined!");
    }
}

sub test_flags {
    return { fatal => 1 };
}

1;
