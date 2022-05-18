argparse 'c/current=' -- $argv
if test -n "$_flag_current"
    set -a excludes --exclude $_flag_current
else
    set -f _flag_current .
end
for arg in $argv
    set -a excludes --exclude $arg
end
set -l stdout (
    begin
        if set -q argv[1] ; printf %s\n $argv ; end
        fd --type file --hidden --follow --strip-cwd-prefix --exclude .git $excludes | proximity-sort $_flag_current
    end | fzf --tiebreak index
)
python3 ~/dev/catherd/kitten-result.py $status "$stdout"
