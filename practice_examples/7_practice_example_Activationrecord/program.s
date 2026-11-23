.text
.globl main
f_square:
    subu $sp, $sp, 4        # PROLOGUE: push $ra
    sw   $ra, 0($sp)
    subu $sp, $sp, 4        # push the caller's $fp
    sw   $fp, 0($sp)
    addiu $fp, $sp, -4      # new frame: 4 bytes
    move $sp, $fp
    sw $a0, 0($fp)          # parameter x from $a0
    lw $t0, 0($fp)          # x
    lw $t1, 0($fp)          # x
    mul $t2, $t0, $t1
    move $v0, $t2           # the result goes in $v0
    j ret_square
ret_square:
    addiu $sp, $fp, 4       # EPILOGUE: drop the frame
    lw    $fp, 0($sp)       # restore the caller's $fp
    addiu $sp, $sp, 4
    lw    $ra, 0($sp)       # restore the return address
    addiu $sp, $sp, 4
    jr    $ra               # back to the caller
f_sumOfSquares:
    subu $sp, $sp, 4        # PROLOGUE: push $ra
    sw   $ra, 0($sp)
    subu $sp, $sp, 4        # push the caller's $fp
    sw   $fp, 0($sp)
    addiu $fp, $sp, -12     # new frame: 12 bytes
    move $sp, $fp
    sw $a0, 0($fp)          # parameter a from $a0
    sw $a1, 4($fp)          # parameter b from $a1
    lw $t0, 0($fp)          # a
    move $a0, $t0           # argument 1
    jal f_square
    move $t0, $v0           # the result
    subu $sp, $sp, 4        # CALL square: save $t0, needed after the call
    sw $t0, 0($sp)
    lw $t1, 4($fp)          # b
    move $a0, $t1           # argument 1
    jal f_square
    move $t1, $v0           # the result
    lw $t0, 0($sp)          # restore $t0
    addiu $sp, $sp, 4
    add $t2, $t0, $t1
    sw $t2, 8($fp)          # s
    lw $t0, 8($fp)          # s
    move $v0, $t0           # the result goes in $v0
    j ret_sumOfSquares
ret_sumOfSquares:
    addiu $sp, $fp, 12      # EPILOGUE: drop the frame
    lw    $fp, 0($sp)       # restore the caller's $fp
    addiu $sp, $sp, 4
    lw    $ra, 0($sp)       # restore the return address
    addiu $sp, $sp, 4
    jr    $ra               # back to the caller
main:
    subu $sp, $sp, 4        # PROLOGUE: push $ra
    sw   $ra, 0($sp)
    subu $sp, $sp, 4        # push the caller's $fp
    sw   $fp, 0($sp)
    addiu $fp, $sp, -0      # new frame: 0 bytes
    move $sp, $fp
    li $t0, 3
    move $a0, $t0           # argument 1
    li $t0, 4
    move $a1, $t0           # argument 2
    jal f_sumOfSquares
    move $t0, $v0           # the result
    move $a0, $t0           # print an integer
    li $v0, 1
    syscall
    li $a0, 10              # print a newline
    li $v0, 11
    syscall
ret_main:
    addiu $sp, $fp, 0       # EPILOGUE: drop the frame
    lw    $fp, 0($sp)       # restore the caller's $fp
    addiu $sp, $sp, 4
    lw    $ra, 0($sp)       # restore the return address
    addiu $sp, $sp, 4
    jr    $ra               # back to the caller
