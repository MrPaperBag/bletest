PASS=$(tr -dc 'A-Za-z0-9' </dev/urandom | head -c7)
spec = $(printf "!@#$%&*+_" | fold -w1 | shuf | head -c1)
pw=$(printf "%s%s" "$PASS" "$spec"  | fold -w1 | shuf )
echo "$pw"

