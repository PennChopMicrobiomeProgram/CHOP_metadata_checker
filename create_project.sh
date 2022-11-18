#!/bin/sh

# @param $1 is the project name
# @param $2 is the client's name
# @param $3 is the client's email

PROJECT_HASH=$(tr -dc a-f0-9 </dev/urandom | head -c 30 ; echo '')

export $(grep -v '^#' CHOP.env | xargs -d '\n')
echo "Creating project...\n" >> $LOG_FP/log.cli

CHECK=$(sqlite3 $DB_FP "SELECT * FROM projects WHERE ticket_code='$PROJECT_HASH';")
if [ -z "${CHECK}" ]; then
  echo "Project code is unique, continuing..."
else
  echo "Project code is not unique, this should be crazy rare, try running the same command again please"
fi

sqlite3 $DB_FP <<EOF
INSERT INTO projects (project_name, contact_name, contact_email, ticket_code) VALUES ('$1', '$2', '$3', '$PROJECT_HASH');
SELECT * FROM projects WHERE ticket_code='$PROJECT_HASH';
EOF

echo "Submission URL: ${URL}/submit/${PROJECT_HASH}"
echo "Created project with\nProject name: ${1}\nClient name: ${2}\nClient email ${3}\nTicket code ${PROJECT_HASH}\n" >> $LOG_FP/log.cli
