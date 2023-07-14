#!/usr/local/bin/perl
use strict;
use warnings;

use Data::Dumper qw(Dumper);
use JSON;
my %_SHARED = ();
####################################################
# Start functions for database from here
####################################################
#CREATE OR REPLACE FUNCTION audio_similarity_functions() RETURNS void
#        AS $$
            $_SHARED{correlation} = sub {
                my @x=@{ $_[0]; };
                my @y=@{ $_[1]; };
                my $len=scalar(@x);
                if (scalar(@x) > scalar(@y)) { 
                   $len = scalar(@y);
                }
                my $covariance = 0;
                my $i, my $bits, my $xor, my $convariance;
                for $i (0..$len-1) {
                   $bits=0;
                   $xor=(int($x[$i]) ^ int($y[$i]));
                   $bits=$xor;
                   $bits = ($bits & 0x55555555) + (($bits & 0xAAAAAAAA) >> 1);
                   $bits = ($bits & 0x33333333) + (($bits & 0xCCCCCCCC) >> 2);
                   $bits = ($bits & 0x0F0F0F0F) + (($bits & 0xF0F0F0F0) >> 4);
                   $bits = ($bits & 0x00FF00FF) + (($bits & 0xFF00FF00) >> 8);
                   $bits = ($bits & 0x0000FFFF) + (($bits & 0xFFFF0000) >> 16);
                   $covariance +=32 - $bits;
                }
                $covariance = $covariance / $len;
                return $covariance/32;
            };
            $_SHARED{crosscorrelation} = sub {
                my @x=@{ $_[0]; };
                my @y=@{ $_[1]; };
                my $offset=$_[2];
                my $min_overlap=$_[3]; #Defaults to span (20)
                if ($offset > 0) {
                    @x = @x[$offset..scalar(@x)-1]
                } if ($offset < 0) {
                    $offset *= -1;
                    @y = @y[$offset..scalar(@y)-1]
                }
                if (scalar(@x)<$min_overlap || scalar(@y) < $min_overlap) {
                    # Error checking in main program should prevent us from ever being
                    # able to get here.
                    return 0;
                 }
                my $correlation = $_SHARED{correlation};
                return &$correlation(\@x, \@y);
            };
            $_SHARED{compare} = sub {
                my @x=@{ $_[0]; };
                my @y=@{ $_[1]; };
                my $crosscorrelation = $_SHARED{crosscorrelation};
                my $span=$_[2];
                if ($span > scalar(@x) || $span > scalar(@y)){
                	$span=scalar(@x)>scalar(@y)? scalar(@y) : scalar(@x);
                	$span--;
                }
                my $min_overlap = $span;
                my @corr_xy, my $offset;
                for $offset (-1*$span..$span){
                	push @corr_xy, &$crosscorrelation(\@x, \@y, $offset, $min_overlap);
                }
                return @corr_xy;
            };
            $_SHARED{maxindex} = sub {
                my @x=@{ $_[0]; };
                my $maxi = 0;
                my $i;
                for $i (1..scalar(@x)-1) {
                	if ($x[$i]>$x[$maxi]) {
                		$maxi = $i;
                	}
                }
                return $maxi;
            };
#        $$
#        LANGUAGE plperl;
#      """)
#    )
#    sqlalchemy.event.listen(
#      db.metadata,
#      'before_create',
#      DDL("""
#        CREATE OR REPLACE FUNCTION get_audio_chromaprint_score(integer[], integer[]) RETURNS float
#        AS $$
sub GetScore { #Remove for DB
            my @first=@{ $_[0]; };
            my @second=@{ $_[1]; };
            if (scalar(@first) > 0 && scalar(@second) > 0 && scalar(@first)*0.8 <= scalar(@second) && scalar(@first)*1.2 >= scalar(@second)) {
                my $span=20;
                my $compare = $_SHARED{compare};
                my @corr = &$compare(\@first, \@second, $span);
                my $maxindex = $_SHARED{maxindex};
                my $max_corr_index = &$maxindex(\@corr);
                return $corr[$max_corr_index]
            }
            return 0.0
} # Remove for DB
#        $$
#        LANGUAGE plperl;


###############
# Main for running from the terminal
##############
my ($first, $second) = @ARGV;
my @listx = decode_json($first);
my @listy = decode_json($second);
print GetScore(@listx,@listy),"\n";
