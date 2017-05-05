#!/bin/bash

LOGFILE=${DEPLOYDIR}/current/log/${RAILS_ENV}.log

function config_replace() {
    # sed -i "s/ddRAILS_ENVdd/${RAILS_ENV}/g" /etc/nginx/sites-available/${APP}
    VAR=$1
    VAL=$2
    FILE=$3
    #    echo evaluating $VAR $VAL $FILE;
    if grep --quiet "dd${VAR}dd" $FILE; then
        echo "setting $VAR to $VAL in $FILE"
        CMD="s/dd${VAR}dd/${VAL}/g"
        sed -i -e ${CMD} ${FILE}
    fi
}

# sed in environmental variables
for ENV in $( env | cut -d= -f1); do
    config_replace "$ENV" "${!ENV}" /etc/nginx/sites-enabled/${APP}
done

# set permission on runtime volumes linked from ${DEPLOYDIR}/current/
cd ${DEPLOYDIR}/shared
for D in cache screenshots projects; do
    chown -R ${DEPLOYUSER}:www-data $D
    chmod -R 775 $D
done

cd -

# perform db migrations at startup
cd ${DEPLOYDIR}/current
su ${DEPLOYUSER} -c 'bundle exec rake db:migrate'

cd -

echo "tailing ${LOGFILE}"
tail -f $LOGFILE &

# normal startup
echo "starting nginx"
echo "--STARTUP FINISHED--"
nginx
