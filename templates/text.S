	/* Code goes into .text section */
	.text
	.global entry
entry:

	/* set need_wakeup to true if reverse_wakeup == 1 */
	move r3, reverse_wakeup
	ld r2, r3, 0
	sub r2, r2, 1
	jump no_need_wakeup, ov

	/* needs wake up */
	st r2, r3, 0 /* reset reverse_wakeup to 0 */
	move r0, need_wakeup /* set need_wakeup to 1 */
	move r1, 1
	st r1, r0, 0

	/* flip the pingpong to move to another round of measurement */
	move r0, pingpong
	ld r1, r0, 0
	sub r1, r1, 1
	jump pingpong_is_1, eq
	move r1, 1
	jump pingpong_end

pingpong_is_1:
	nop
	move r1, 0

pingpong_end:
	st r1, r0, 0

no_need_wakeup:

	/* increment run count */
	move r0, pingpong
	ld r0, r0, 0
	sub r0, r0, 1
	jump increment_run_count_pp1, eq

	move r3, run_cnt_pp0
	jump increment_run_count_end

increment_run_count_pp1:
	move r3, run_cnt_pp1
	nop

increment_run_count_end:
	ld r2, r3, 0
	add r2, r2, 1
	st r2, r3, 0

	/* Control logic starts
		switch (step) {
{{			case [x]:
				goto step_[x];}}
		}
	*/
	move r1, step
	ld r1, r1, 0
	add r1, r1, 1

{{	/* check [x] */
	sub r1, r1, 1
	jump step_[x], eq
}}

no_work:
	sleep 0 /* use sleep period set in SENS_ULP_CP_SLEEP_CYC0_REG */


/* ------------------ GENERAL STATE UPDATE FUNCTIONS ------------------ */
increment_step:
	/*
		step++;
		if (step < n_clusters)
			goto check_wake_up;
		step = 0;
	*/
	move r1, step
	ld r0, r1, 0
	add r0, r0, 1
	st r0, r1, 0
	sub r0, r0, n_clusters
	jump check_wake_up, ov
	st r0, r1, 0

	/* Increment cycle
		cycle++;
		if (cycle < period)
			goto check_wake_up;
		cycle = 0;
	*/
	move r1, cycle
	ld r0, r1, 0
	add r0, r0, 1
	st r0, r1, 0
	sub r0, r0, period
	jump check_wake_up, ov
	st r0, r1, 0

/* ------------------ WAKE UP AND EXIT FUNCTIONS ------------------ */

check_wake_up:
	/*
		if (need_wakeup == 0)
			goto exit;
	*/
	move r0, need_wakeup
	ld r0, r0, 0
	sub r0, r0, 1
	jump wake_up, eq

	/* value within range, end the program */
	.global exit
exit:
	halt

/* ------------------ WAKE UP FUNCTIONS ------------------ */
	.global wake_up
wake_up:

	/* Check if the system can be woken up */
	READ_RTC_REG(RTC_CNTL_DIAG0_REG, 19, 1)
	and r0, r0, 1
	jump exit, eq

	/* reset need_wakeup */
	move r0, need_wakeup
	move r1, 0
	st r1, r0, 0

	/* Wake up the SoC, end program */
	wake
	halt

/* ------------------ PER STEP FUNCTIONS ------------------ */

{{step_[x]:
	/*
		cycle_[x]++;
		if (cycle_[x] < period_[x])
			goto no_work;
		cycle_[x] = 0;
	*/
	move r1, cycle_[x]
	ld r0, r1, 0
	add r0, r0, 1
	st r0, r1, 0
	sub r0, r0, period_[x]
	jump no_work, ov
	st r0, r1, 0

	sleep [d] /* use sleep period set in SENS_ULP_CP_SLEEP_CYC[d]_REG */

	/* Execute the code of sensor group [x] */

	move r0, pingpong
	ld r0, r0, 0
	sub r0, r0, 1
	jump increment_run_count_pp1_[x], eq

	move r1, run_cnt_pp0_[x]
	jump increment_run_count_end_[x]

increment_run_count_pp1_[x]:
	move r1, run_cnt_pp1_[x]
	nop

increment_run_count_end_[x]:

	ld r0, r1, 0
	add r0, r0, 1
	st r0, r1, 0

[code]

	/* After finishing execution */
	jump increment_step
}}