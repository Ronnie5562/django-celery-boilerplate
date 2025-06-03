#!/usr/bin/env bash

if [ $# -ne 2 ]; then
    echo "Usage: $0 <commit_message> <file_name_or_dot>"
    exit 1
fi

commit_message="$1"
file_name="$2"

if [ "$file_name" != "." ] && [ ! -e "$file_name" ]; then
    echo "File '$file_name' not found."
    exit 1
fi

git add "$file_name"

git commit -m "$commit_message"

git push origin main  # Change 'main' to your branch name to contribute

if [ $? -eq 0 ]; then
    echo -e "\e[32mPush successful!\e[0m"
else
    echo -e "\e[31mFailed to push changes. Please check your network connection and try again.\e[0m"
fi