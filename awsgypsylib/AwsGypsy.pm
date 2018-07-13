#!/usr/local/bin/perl

package AwsGypsy;

require Exporter;
@ISA = qw(Exporter);
@EXPORT = qw(new getAcct);




sub new {
  my $class = shift;
  my %params = @_;
  my $self = {};
  bless $self, $class;

  #####root config dir block####### 
  $AwsGypsy::root_configdir = "";
  #this begin block sets the root_configdir and lets you change it with an eviroment variable in your .bashrc
  $AwsGypsy::root_configdir = "~/.aws/awsgypsy";
  if ($ENV{'awsgypsy_root_configdir'}){
  	$AwsGypsy::root_configdir = $ENV{'awsgypsy_root_configdir'};
  	}
  if ($AwsGypsy::root_configdir =~ /^~/){
  	$AwsGypsy::root_configdir =~ s/^~/$ENV{'HOME'}/g;
  	}
  #print "checking for $AwsGypsy::root_configdir\n";
  if (-d $AwsGypsy::root_configdir) {
	print "$AwsGypsy::root_configdir is a directory\n" if $::DEBUG<1;
	}
  elsif (-e $AwsGypsy::root_configdir) {
	print "DANGER WILL ROBINSON!!!!  $AwsGypsy::root_configdir exists and is not a directory\n";
	exit(0);
	}
  else {
	$::DEBUG = 1; #set debug since it's the first time using the script
	print "awsgypsy_root_configdir of ",$AwsGypsy::root_configdir," does not exist, but it's ok, I know how to make it\n";
	mkdir($AwsGypsy::root_configdir,0700) || die "Could not make the directory $AwsGypsy::root_configdir :$!\n";
	}
  #####end root config dir block####### 

  ####get acct number block######
  #if no account number is given take it from default
  my $default_file = "$AwsGypsy::root_configdir/default_account";
  if (!$params{'acct'}){
	print "acct was not passed in\n" if $::DEBUG<1;
	if (-e "$default_file"){
		open(DEF, "$default_file") or die "can't open default_account file: $!\n";
		$params{'acct'} = <DEF>;
		chomp $params{'acct'};
		close DEF;
		print "aquired acct from default_account: $params{'acct'}\n" if $::DEBUG<1; 
		}
	else {
		while (!$params{'acct'}){
			print "What aws account are you trying to run against?: ";
			$params{'acct'} = <STDIN>;
			$params{'acct'} =~ s/\s*//g;
			}
		}
	}
  #if an account number is given and there is no default, make it the new default
  if (! -e "$default_file"){
	open(DEF, ">$default_file") or die "can't open $default_file  for write: $!\n";
	print DEF $params{'acct'};
	close DEF;
	print "saved $params{'acct'} to default file\n";
	}
  ####end get acct number block######

  #set the account number to self and the config dir
  $self->{'acct'} = $params{'acct'};
  $self->{'config_dir'} = "$AwsGypsy::root_configdir/$params{'acct'}";


  if (! -e "$self->{'config_dir'}"){
	mkdir "$self->{'config_dir'}";
        $params{'acct'} =~ s/\D*//g;
	open(ACCT,">$self->{'config_dir'}/account_number") or die "Can't open $self->{'config_dir'}/account_number for writing: $!\n";
	print ACCT $params{'acct'};
	close ACCT;
	print "If you would like a user friendly name for this account type it here, hit enter to just use the numbers: ";
	my $alias = <STDIN>;
	$alias =~ s/\s*//g;
	$alias =~ s/\*//g;
	$alias =~ s/;//g;
	if ($alias){
		if (-e "$AwsGypsy::root_configdir/$alias"){
			print "That Alias is taken, skipping alias, if you'd like to make one just go to $AwsGypsy::root_configdir and make a softlink to $self->{'config_dir'}\n";
			}
		else {
			print "ok, saving $param{'acct'} as $alias, you may use the two names interchangably\n";
			print "linking ","$self->{'config_dir'}"," to ", "$AwsGypsy::root_configdir/$alias","\n";
			system ("ln -s $self->{'config_dir'} $AwsGypsy::root_configdir/$alias");
			#TODO: the link function said operation not permited, don't know why, but the system call works for now... keep on bailing
			#link "$self->{'config_dir'}", "$AwsGypsy::root_configdir/$alias" or die "failed to link: $!\n";
			}
		}
	#maybe we should initiate a config here?
	}



  open(ACCT,"$self->{'config_dir'}/account_number") or die "Can't open $self->{'config_dir'}/account_number: $!\n";
  $self->{'acct_num'} = <ACCT>;
  $self->{'acct_num'} =~ s/\D*//g;
  close ACCT;

  die "no account number saved to fix this, manually edit the file $self->{'config_dir'}/account_number and put the aws account number in it" if !$self->{'acct_num'};

  $self->{'apps'} = {};


  #and again with the bless.
  return $self;
}


sub getAcct {
	return $self->{'acct'};
	}


sub configure_apps {
	
	}

sub read_config {

	}





1;
