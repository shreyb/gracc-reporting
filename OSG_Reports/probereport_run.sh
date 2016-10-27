#!/bin/sh

STARTDATE=`date --date='2 week ago' +"%F %T"`

cd /home/gratia/gracc_email_reports/OSG_Reports

echo "START" `date` >> probereport_run.log

python ProbeReport.py -d -e $STARTDATE

if [ $? -ne 0 ]
then
    echo "Error running report.  Please try running the report manually" >> probereport_run.log
else
    echo "Sent report" >> probereport_run.log
fi


echo "END" `date` >> probereport_run.log