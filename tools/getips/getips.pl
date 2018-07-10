#!/usr/local/bin/perl

die "no address given" if !$ARGV[0];
my $ipsrc = $ARGV[0];

open(IPS,"curl $ipsrc &> /dev/stdout |") or die "can't curl the list of ips";

%ips = ();


@intranetips = qw(10 172 192);

my $inblock = 1;
my $startstring = $ARGV[1];
my $endstring = $ARGV[2];
if ($startstring) { $inblock = 0; }

#print "Searching for IP's in:\n\t$ipsrc\n\nStarting at string: $startstring\nEnding at string: $endstring\nInBlock is set to: $inblock\n\n";



while ($line = <IPS>) {
	if ($startstring && !$inblock && $line =~ /$startstring/) {
		#print "Starting In Block: $line\n";
		$inblock = 1;
		}
	elsif ($startstring && $endstring && $inblock && ($line =~ /$endstring/)) {
		#print "Ending In Block: $line\n";
		$inblock = 0;
		}
	elsif ($inblock){
		if (my @matches = $line =~ m{ ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\/[0-9]{1,5}) }xmsg) {
			#print qq{@matches};
			foreach my $ipblock (@matches){
				my $intranet = 0;
				foreach $iip (@intranetips){ if ($ipblock =~ /^$iip\./){ $intranet = 1; } }
				if (!$intranet) {
					$ips{$ipblock} = 1;
					}
				}
			}
		}
	}


foreach my $ipblock (sort keys %ips){
	print $ipblock,"\n";
	}



