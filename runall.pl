#!/usr/local/bin/perl

use lib 'lib/';
use AwsGypsy;
use JSON;
use Data::Dumper;

$::DEBUG = 2;
# Debug levels:
#    0 - Developer
#    1 - Debug my config (or first time run)
#    2 - warn me of things I might care about
#    3 - general logs
#    4 - only inportant things
#    5 - Shut up I don't care what you have to say
#



$awsgypsy = AwsGypsy->new('acct' => @ARGV[0] );
debug("Starting AwsGypsy for $awsgypsy->{'acct'} ($awsgypsy->{'acct_num'})\n",4);
debug("Using a config_dir for all awsgypsy configs of " . $awsgypsy->{'config_dir'},1);


#####make sure all variables are configured####
#at this point we should search the tree strucutre for VAR files
print "....loading configs and configuring apps that don't have values.....\n\n" if $::DEBUG<4;
loadconf('apps');
checkdir(".",'CONF');
saveconf('apps');
print "....running your apps.....\n\n" if $::DEBUG<4;
checkdir(".",'RUN');








sub loadconf {
	my ($conf) = @_;
	my $conffile =  $awsgypsy->{'config_dir'} . "/$conf" . '.json';
	if (-e $conffile){
		my $confval = '';
		open(my $C,"$conffile") or die "can't open $conffile : $!\n";
		while (<$C>){$confval .= $_;}
		close($C);
		my $json = JSON->new;
		$awsgypsy->{$conf} = $json->decode($confval);
		print "********LOADED*******$conf******\n",$json->pretty->encode($awsgypsy->{$conf}),"\n********LOADED*******$conf******\n" if $::DEBUG<1;
		}
	else {
		$awsgypsy->{$conf} = ();
		}
	}
	

sub saveconf {
	my ($conf) = @_;
	my $json = JSON->new;
	my $confval = $json->pretty->encode($awsgypsy->{$conf});
	my $conffile =  $awsgypsy->{'config_dir'} . "/$conf" . '.json';
	print "My Conffile is $conffile\n" if $::DEBUG<1;
	open(my $C,">$conffile") or die "can't open $conffile for writing: $!\n";
	print $C $confval;
	close($C);

	}


sub checkdir {
	my ($path,$cmd) = @_;
	opendir my $dir, $path  or die "Cannot open directory: $!";
	my @files = readdir $dir;
	closedir $dir;
	foreach $file (@files){
		next if $file =~ /^\./;;
		my $fqn = "$path/$file";
		#print "$fqn\n";
		if (-d $fqn){
			checkdir($fqn,$cmd);
			}
		elsif ((($file eq 'VARS') && ($cmd eq 'CONF')) && !$awsgypsy->{'apps'}{$path}){ 
			config_vars($path);
			}
		elsif (($file eq 'RUN') && ($cmd eq 'RUN')) {
			if ( $awsgypsy->{'apps'}{$path}{'enabled'}{'value'} eq true ){ 
				open(my $runme, $fqn) or die "Can't read $fqn: $!\n";
				my $runcmd = <$runme>;
				close($runme);
				my %cmdvars = (
					'config_dir' => $awsgypsy->{'config_dir'},
					'path' => $path
					);
				foreach my $k (keys %{ $awsgypsy->{'apps'}{$path}{'vars'} } ){
					$cmdvars{$k} = $awsgypsy->{'apps'}{$path}{'vars'}{$k}{'value'};
					}
				$runcmd =~ s/\{\{(.*?)\}\}/$cmdvars{$1}/g;	
				print "running: $runcmd\n" if $::DEBUG<4;
				system($runcmd);
			} else {
				print "not running $path because it is not enabled\n" if $::DEBUG<4;
				}

			}



		}
	}



sub config_vars {
	my ($path) = @_;
	#create the place holder for config info
	my %thisapp = ();
	my $confchanged = 0;

	print "need to config $path\n\n";

	my $desc_file = "$path/DESC";
	open (my $desc, $desc_file) or die "Can't open $desc_file: $!\n";
	while (my $line = <$desc>) {print $line;} 
	print "\n\n";
	close($desc);

	print "Would you like to enable $path? [Yes/No]: ";
	my $enabled = <STDIN>;
	$enabled =~ s/\s*//g;
	$awsgypsy->{'apps'}{$path}{'enabled'} = ();

	if ((lc(substr $enabled, 0, 1)) eq 'y'){

		$awsgypsy->{'apps'}{$path}{'enabled'} = { 'value' => true, 'src' => 'conf'};
		my $vars_file = "$path/VARS";
		print "reading $vars_file\n";
		open(my $vars,$vars_file) or die "can't open $vars_file for read: $!\n";
		while (my $line = <$vars>){
			chomp $line;
			my ($req,$varname,$question) = (split(/:/,$line));
			my $opt = '';
			my $val = '';
			if (lc($req) ne 'required'){ $opt = "(optional) "; }
			do {
				print "$question $opt: ";
				$val = <STDIN>;
				chomp $val;
				print "\n";
				if ($val){
					$thisapp{$varname} = {};
					$thisapp{$varname}{'value'} = $val;
					$thisapp{$varname}{'src'} = 'conf' ;
					$confchanged = 1;
					}
			} until (( (lc($req) eq 'required') && $val ) || (lc($req) ne 'required'));



			}


		if ($confchanged){
			$awsgypsy->{'apps'}{$path}{'vars'} = ();
			%{ $awsgypsy->{'apps'}{$path}{'vars'} }= %thisapp;
			}



		}
	else {
		$awsgypsy->{'apps'}{$path}{'enabled'} = { 'value' => false, 'src' => 'conf'};
		}
	
	}



sub debug {
	my ($msg,$lvl) = @_;
	if ($::DEBUG <= $lvl){
		print $msg,"\n";
		}
	}

