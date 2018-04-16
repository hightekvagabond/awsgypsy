#!/usr/local/bin/perl

use lib 'lib/';
use AwsGypsy::Config;

$::DEBUG = 0;
# Debug levels:
#    0 - Developer
#    1 - Debug my config (or first time run)
#    2 - warn me of things I might care about
#    3 - general logs
#    4 - only inportant things
#    5 - Shut up I don't care what you have to say
#



$awsgypsy = AwsGypsy::Config->new('acct' => @ARGV[0] );

debug("Using a configdir for all awsgypsy configs of " . $awsgypsy->{'config_dir'},1);




sub debug {
	my ($msg,$lvl) = @_;
	if ($::DEBUG <= $lvl){
		print $msg,"\n";
		}
	}

