#!/usr/local/bin/perl

die "no address given" if !$ARGV[0];

open(IPS,"curl $ARGV[0] &> /dev/stdout |") or die "can't curl the list of ips";

%ips = [];

while ($line = <IPS>) {
print $line;
	if (my @matches = $line =~ m{ ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\/[0-9]{1,5}) }xmsg) {
   		#print qq{@matches};
		foreach my $ipblock (@matches){
			if (($ipblock =~ /^10\./) || ($ipblock =~ /^172\./)) {
				#do nothing
				}
			else {
				$ips{$ipblock} = 1;
				}
			}
		}
	}

foreach my $ipblock (keys %ips){
	print $ipblock,"\n";
	}



