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

use base "basetest";
use strict;
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

    # if systemd-analyze blame fails, then the pipe swallows the error
    # setting pipefail remedies that
    assert_script_run('set -o pipefail');
    assert_script_run('systemd-analyze blame | head -n 15');
}

sub test_flags {
    return { fatal => 1 };
}

1;
