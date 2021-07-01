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
    # in case we are not booting from an ISO, then eject the CD, so that openQA
    # cannot boot from it
    # in case REBOOT is not 1, then the cd has already been ejected and we don't
    # need to remove it again
    if (get_var('HDD_1') && (get_var('REBOOT', 0) == 0)) {
        eject_cd(id => 'cd1-device', force => 1);
    }

    # if we are rebooting, then we have to wait longer as the system is shutting
    # down (which also takes a bit)
    my $bootloader_timeout = get_var('REBOOT', 0) ? 30 : 10;

    # we first check whether the bootloader is visible (fails on Fedora for
    # $reasons...)
    my $match = check_screen('kiwi_bootloader', timeout => $bootloader_timeout);
    if ((get_var('DISTRI') eq 'fedora') && (defined(get_var('HDD_1'))) && (!defined($match))) {
        record_soft_failure('No visible bootloader in the Fedora disk images');
    } elsif (get_var('UEFI') && !defined($match)) {
        my $distri = get_var('DISTRI');
        my $version = get_var('VERSION');
        record_soft_failure("bootloader is not visible for $distri $version in UEFI mode");
    } elsif (!defined($match)) {
        die "Did not see the bootloader";
    }

    # Check now whether we have to handle UEFI certificates or whether the
    # bootloader is at the wrong entry or whether we have to enter the LUKS
    # passphrase
    # We do this in a second check_screen, to ensure that the matched needle
    # will not be "just" 'kiwi_bootloader'.
    check_screen([qw(kiwi_bootloader_boot_from_hdd trust_uefi_certificates enter_luks_passphrase)]);

    if (match_has_tag('enter_luks_passphrase')) {
        type_string('linux');
        send_key('ret');
    }

    if (match_has_tag('trust_uefi_certificates')) {
        die 'trust UEFI certificates screen present, but UEFI is not used' unless defined(get_var('UEFI'));

        send_key('down') if match_has_tag('trust_uefi_certificates_no');

        assert_screen('trust_uefi_certificates_yes');
        send_key('ret');

        assert_screen([qw(kiwi_bootloader kiwi_bootloader_boot_from_hdd)]);
    }

    # for some live images the default selected boot entry is the "Boot from
    # Hard Disk" entry we don't want that, so we need to select the correct
    # entry that says "Install $NAME" to achieve that, we just hit HOME first
    # which gets us to the first entry and then spam down until we get a needle
    # match
    if (match_has_tag('kiwi_bootloader_boot_from_hdd') && defined(get_var('PUBLISH_HDD_1'))) {
        send_key('home');
        send_key_until_needlematch('kiwi_bootloader_install_selected', 'down', 10);
        send_key('ret');
    }

    # wait 10 minutes for the unattended installation and 2 for a regular boot
    # (booting can take a while for appliances based on MicroOS as ignition
    # takes its time)
    my $timeout = defined(get_var('PUBLISH_HDD_1')) ? 600 : 120;

    # appliances based on MicroOS will spend a loooong time installing &
    # verifying the disk image
    assert_screen([qw(login_prompt installation_screen)], $timeout);

    # => if we see the installation screen, then wait again for up to ten
    # minutes for it to finally finish installation & disk verify
    if (match_has_tag('installation_screen')) {
        die "Saw the installation screen on the second boot" if get_var('REBOOT', 0) == 1;
        assert_screen('login_prompt', 600);
    }
}

sub test_flags {
    # without anything - rollback to 'lastgood' snapshot if failed
    # 'fatal' - whole test suite is in danger if this fails
    # 'milestone' - after this test succeeds, update 'lastgood'
    # 'important' - if this fails, set the overall state to 'fail'
    return { fatal => 1 };
}

1;
