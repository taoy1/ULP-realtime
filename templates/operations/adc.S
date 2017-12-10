	adc r0, 0, adc_channel + 1 /* See example in examples/system/ulp_adc of esp32 repository */

	/* Store r0 in circular buffer */
{if is_pingpong}
	move r1, pingpong
	ld r1, r1, 0
	sub r1, r1, 1
	jump [s]_pingpong1, eq

	/* use pingpong buffer 0 */
	move r1, out_buf_pp0		/* r1 = &out_buf_pp0 */
	move r3, out_idx_pp0		/* r3 = &out_idx_pp0 */
	jump [s]_pingpong_end

[s]_pingpong1:
	/* use pingpong buffer 1 */
	move r1, out_buf_pp1		/* r1 = &out_buf_pp1 */
	move r3, out_idx_pp1		/* r3 = &out_idx_pp1 */
	jump [s]_pingpong_end

[s]_pingpong_end:

{else}
	move r1, out_buf		/* r1 = &out_buf */
	move r3, out_idx		/* r3 = &out_idx */
{endif}

	ld r2, r3, 0			/* r2 = out_idx */
	add r1, r1, r2			/* r1 = r1 + r2 */
	st r0, r1, 0			/* out_buf[out_idx] = r0 */
	add r2, r2, 1			/* r2 = r2 + 1 */
	st r2, r3, 0			/* out_idx = r2 */
	sub r2, r2, out_bufsize /* r2 = r2 - out_bufsize */
	jump [s]_adc_l1, ov		/* if r2 < 0, goto [s]_adc_l1 */

	/* if branch is false */
	st r2, r3, 0			/* out_idx = r2 */
	jump [s]_adc_end		/* 2 instructions after the branch */

	/* if branch is true */
[s]_adc_l1:
	nop						/* 3 nops after the branch, keeping the */
	nop						/* number of instructions the same */
	nop

[s]_adc_end:

