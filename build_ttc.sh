PYTHON="python3"
TUPTINYCOMPILER="tuptiny_compiler.py"
C_COMPILER="gcc"

function comp {
    BASENAME=$( basename -s .tup $1 )
    TUPTINYCOMPILER_OUT=$(${PYTHON} ${TUPTINYCOMPILER} $1 2>&1)
    if [ $? -ne 0 ]; then
        echo "${TUPTINYCOMPILER_OUT}"
    else
        mv TTC_Output/ttc_out.c TTC_Output/${BASENAME}.c
        C_COMPILER_OUT=$(${C_COMPILER} -o ExecutableCode/${BASENAME} TTC_Output/${BASENAME}.c)
        if [ $? -ne 0 ]; then
            echo "${C_COMPILER_OUT}"
        else
            echo "${TUPTINYCOMPILER_OUT}"
        fi
    fi
}

if [ $# -eq 0 ]; then
    for i in $( ls SourceFiles/*.tup ); do
        comp $i
    done
else
    comp $1
fi