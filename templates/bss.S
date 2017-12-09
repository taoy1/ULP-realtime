	/* Define variables, which go into .bss section (zero-initialized data) */
	.bss

	/* Time_up marker set by the main program. */
	.global reverse_wakeup
reverse_wakeup:
	.long 0

	/* States */

step:
	.long 0
cycle:
	.long 0
need_wakeup:
	.long 0

	/* Counter of ULP run */
	.global run_cnt_pp0
run_cnt_pp0:
	.long 0
	.global run_cnt_pp1
run_cnt_pp1:
	.long 0

