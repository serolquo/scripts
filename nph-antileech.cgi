#!/usr/local/bin/perl

#########################################################################
# PROGRAM: SPEED AND MAX DOWNLOAD LIMIT                                 #
# Description: This program will allow you to limit the max transfer    #
#              speed and the max amount of downloads                    #
# Version History:                                                      #
#      1.3 enable max download per person                               #
#      1.2 Resumes Support                                              #
#      1.1 Major Revision                                               #
#          Totally re-wrote script                                      #
#   	   use PID to check for current connections                       # 
#      1.0 Initial Release                                              #
#########################################################################



######  SETTING VARIABLES DECLARATIONS  ############
$cgifile = "nph-antileech.cgi";
$buffer = 24336;  #max speed in byte/sec only good if speed limit is turned on
$maxConnect = 10;  #max number of downloads
$maxPerPerson = 1;  #max number of downloads per person
$speedLimit = 1;  #turn speed limit on or off
$fileLoc = "/usr/home/user/file/"; #location where content files are
$fileSettingLoc = "/usr/home/user/stats/"; #used for logs
@allowableDomains = ("http://example1.com", "http://example2.com");
##### END OF changeable variables


$count = -3;
$currentPerson = 0;
$loopNumber = 0;
$filename =  $ENV{'QUERY_STRING'};
$refFile = "referer.txt";
$badRef = "badref.txt";
$defaultPid = "pid.blah";


if (index($filename, "..") ne -1)
{	
	&PrintHeader("Bad filename...", 1, "HTTP/1.1 404 File Not Found");
	goto ENDPROGRAM;
}

substr($filename,0,0) = $fileLoc;
substr($refFile, 0, 0) = $fileSettingLoc;
substr($badRef, 0, 0) = $fileSettingLoc;
substr($defaultPid, 0, 0) = $fileSettingLoc;
$refCode = 0;
##### END of variables declarations  ######

&UpdatePid;

### check to see how many people are currently downloading ###

if ($count >= $maxConnect)
{
	&PrintHeader("Too many downloads...", 1, "HTTP/1.1 404 File Not Found");
	goto ENDPROGRAM;
}

if ($currentPerson >= $maxPerPerson)
{
	&PrintHeader("You're already downloading...", 1, "HTTP/1.1 404 File Not Found");
	goto ENDPROGRAM;
}

### calls check reference, could be expanded to block out bad webmasters ###
&RefCheck;
if ($refCode ne 1)
{
	&PrintHeader("BAD REFERER, Please close down your browser and try again using www.yoursite.com", 1, "HTTP/1.1 401 Unauthorize");
	goto ENDPROGRAM;
}


### This will check the file name####
$position = rindex($filename, "/") + 1;
if ($position eq 0)
{
	$file = $filename;	
}
else
{
	$file = substr($filename, $position);	
}

### opens file for send ###
unless (open(FILE, $filename))
{
    &PrintHeader("File does not exist", 1, "HTTP/1.1 404 Not Found");
    goto ENDPROGRAM;
}	

&resume;
&PrintHeader($file, 0);
&CreatePid;
&SendFile;
&DestroyPid;

goto ENDPROGRAM;

### Prints the appropreate header or error message ###
sub PrintHeader
{
	my($head, $error, $type) = @_;
	if ($error eq 0)
	{
		print "Content-Disposition: filename=$head\n";
		print "Content-type: application/octet-stream\n\n";
	}
	else
	{
		print "$type\n";
		print "Content-type: text/html\n\n";
		print "<HTML><HEAD><TITLE>ERROR</TITLE></HEAD><BODY>";
		print "<H3>$head</H3>";
		print "</BODY></HTML>"; 
	}
}


### Sendfile Sub, send the file ###
sub SendFile
{
    while (!eof(FILE))
    {
    	$skipChars = tell(FILE);
    	seek(FILE, $skipChars, 0);
    	read(FILE, $filecontent, $buffer);
    	$skipChars += $buffer;
    	if ($filecontent ne "")
    	{
        	print($filecontent);
        	$filecontent = "";
    	}
    	else 
    	{last;}
        if ($speedLimit eq 1)
        {sleep 1;}

    }
}

### Sub for logging and checking referer ###
sub RefCheck
{
	open(REFERER, ">>$refFile");
	my ($sec, $min, $hour, $day, $mon, $year) = localtime();
	seek(REFERER, 0, 2);
	print REFERER "[$year/$mon/$day - $hour:$min:$sec] - ";
	print REFERER "$ENV{'REMOTE_ADDR'} - $ENV{'HTTP_USER_AGENT'} - ";
	print REFERER "$ENV{'HTTP_REFERER'} - $ENV{'QUERY_STRING'}\n";
	close(REFERER);
	foreach $domain (@allowableDomains)
	{
		if (index($ENV{'HTTP_REFERER'}, $domain) ne -1)
		{
			$refCode = 1;
			last;
		}
		else
		{
			$refCode = 0;
		}
	}
	if ($ENV{'HTTP_REFERER'} eq "")
	{
		$refCode = 1;	
	}
	if ($refCode eq 0)
	{
		open(BADREF, ">>$badRef");
		seek(BADREF, 0, 2);
		print BADREF "[$year/$mon/$day - $hour:$min:$sec] - $ENV{'HTTP_REFERER'}\n";
		close(BADREF);	
	}
}

sub resume
{
	$resumePos = 0;
	my($position) = rindex($ENV{'HTTP_RANGE'}, "=")+1;
	$resumePos = substr($ENV{'HTTP_RANGE'}, $position);
	$position = rindex($resumePos, "-");
	$resumePos = substr($resumePos, 0, $position);
	seek(FILE, 0, 2);
	my($fileSize) = tell(FILE);
	my($size) = $fileSize;
	my($secondlastbyte) = $fileSize - 1;
	if ($resumePos ne "")
	{	
		print "HTTP/1.1 206 Partial Content\n";
		if ($resumePos >= 0)
		{
			$size = $fileSize-$resumePos;
			seek(FILE, $resumePos, 0);		
			print "Content-range: bytes $resumePos-$secondlastbyte/$fileSize\n";
			print "Content-length: $size\n";
		}
	}
	else
	{
		seek(FILE, 0, 0);
		print "HTTP/1.1 200 OK\n";
		print "Content-range: bytes 0-$secondlastbyte/$fileSize\n";
		print "Content-length: $fileSize\n";
	}
}

sub CreatePid
{
	$pid = getppid();
	$pidfile = ".pid";
	substr($pidfile, 0, 0) = $pid;
	substr($pidfile, 0, 0) = $fileSettingLoc; 
	system("cp", "$defaultPid", "$pidfile");
	system("chmod", "777", "$pidfile");
	open(PIDFILE, ">$pidfile");
	print PIDFILE "$pid $ENV{'REMOTE_ADDR'} $file\n";
	close(PIDFILE);
}

sub DestroyPid
{
	system("rm", "$pidfile");
}

sub UpdatePid
{
	my($AllPidFile) = "*.pid";
	substr($AllPidFile, 0, 0) = $fileSettingLoc;
	
	open(DOWNLOADS, "ps -ef | grep $cgifile|");
	@sysPid = <DOWNLOADS>;
	close(DOWNLOADS);
    
    ### this loop will update the total current download
    ### it will also strip the pipe down to just the PIDs
    foreach $tPid (@sysPid)
    {
		$count++;
    }
    open(PIDFILE, "cat $AllPidFile|");
       
    ### this loop will attempt to delete expired PID files
    ### it will also update the current number of download per person
    do
    {
    	$fileExist = 0;
    	$pidfile = ".pid";
    	$pidcontent = <PIDFILE>;
    	@bPid = split(/ +/, $pidcontent);
    	$pidfromfile = $bPid[0];
    	
    	### now it will check for expire pid files
    	foreach $tPid (@sysPid)
    	{
    		if (index($tPid, $pidfromfile) ne "-1")
    		{
    			$fileExist = 1;
    			## this will return the current # of downloads per person
    			$clientIP = @bPid[1];
    			if ($clientIP eq $ENV{'REMOTE_ADDR'})
    				{ $currentPerson++; }
    			last;
    		}
    		else
    			{$fileExist = 0;}
    	}
    	### this will delete expired pid file
    	if ($fileExist eq 0)
    	{
    		substr($pidfile, 0, 0) = $pidfromfile;
    		substr($pidfile, 0, 0) = $fileSettingLoc;
    		system("rm", "$pidfile");
    	}
    } while($pidcontent ne "");
    close(PIDFILE);
}

ENDPROGRAM:
#die "blah";
