<</* This assembly is the assembly of the following pesudo code:
 *
 * sum = 0;
 * for (i = 0; i < in_bufsize; ++i) {
 *		sum += in_buf[i];
 * }
 * out_buf[out_idx] = sum;
 * out_idx++;
 * if (out_idx == out_bufsize) {
 *		out_idx = 0;
 * }
 */>>

	move r1, in_buf			/* r1 = &in_buf */
	move r0, 0				/* r0 = accumulator */

{{	ld r2, r1, [4d] 			/* r2 = in_buf[0:in_bufsize] */
	add r0, r0, r2			/* r0 += r2 */}}

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
	jump [s]_sum_l1, ov		/* if r2 < 0, goto [s]_sum_l1 */

	/* if branch is false */
	st r2, r3, 0			/* out_idx = r2 */
	jump [s]_sum_end		/* 2 instructions after the branch */

	/* if branch is true */
[s]_sum_l1:
	nop						/* 3 nops after the branch, keeping the */
	nop						/* number of instructions the same */
	nop

[s]_sum_end:
