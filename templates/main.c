#include <stdio.h>
#include <string.h>
#include "esp_sleep.h"
#include "nvs.h"
#include "nvs_flash.h"
#include "soc/rtc_cntl_reg.h"
#include "soc/sens_reg.h"
#include "driver/gpio.h"
#include "driver/rtc_io.h"
#include "driver/adc.h"
#include "driver/dac.h"
#include "esp32/ulp.h"
#include "ulp_ulptest.h"
#include "esp_sleep.h"
#include <sys/time.h>

extern const uint8_t ulp_main_bin_start[] asm("_binary_ulp_ulptest_bin_start");
extern const uint8_t ulp_main_bin_end[]   asm("_binary_ulp_ulptest_bin_end");

/* This function is called once after power-on reset, to load ULP program into
 * RTC memory and configure the ADC.
 */
static void init_ulp_program();

/* This function sets a marker in the ULP program so that ULP will wake up CPU */
static void trigger_reverse_wakeup_ulp_program();

/* This function is called every time before going into deep sleep.
 * It starts the ULP program and resets measurement counter.
 */
static void reset_ulp_program();

void start_ulptest()
{
    esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
    switch (cause) 
    {
        case ESP_SLEEP_WAKEUP_TIMER:
            printf("****Timer wakeup****\n\n");
            break;
        case ESP_SLEEP_WAKEUP_ULP:
            printf("****Deep sleep wakeup****\n\n");
            break;
        default:
            printf("****Initial wakeup****\n\n");
            break;
    }

    if (cause == ESP_SLEEP_WAKEUP_ULP) {
        printf("Pingpong buffer of current measurement is #%d\n", (ulp_pingpong & UINT16_MAX) == 1 ? 0 : 1);
        
        if ((ulp_pingpong & UINT16_MAX) == 1) {
            printf("Last measurement:\n");
            printf("ULP ran %d times\n", ulp_run_cnt_pp0 & UINT16_MAX);
{{          printf("Cluster [x] ran %d times\n", ulp_run_cnt_pp0_[x] & UINT16_MAX); }}
            printf("Ongoing measurement has run %d times\n", ulp_run_cnt_pp1 & UINT16_MAX);
        } else {
            printf("Last measurement:\n");
            printf("ULP ran %d times\n", ulp_run_cnt_pp1 & UINT16_MAX);
{{          printf("Cluster [x] ran %d times\n", ulp_run_cnt_pp1_[x] & UINT16_MAX); }}
            printf("Ongoing measurement has run %d times\n", ulp_run_cnt_pp0 & UINT16_MAX);
        }
    }

    struct timeval tv;
    gettimeofday(&tv, NULL);
    printf("current time is %ld %ld\n\n" , tv.tv_sec, tv.tv_usec);
    printf("Entering deep sleep\n\n");

    switch (cause) 
    {
        case ESP_SLEEP_WAKEUP_TIMER:
            trigger_reverse_wakeup_ulp_program();
            printf("Completed one round of measurement\n");
            break;
        case ESP_SLEEP_WAKEUP_ULP:

            reset_ulp_program();
            ESP_ERROR_CHECK( esp_sleep_enable_timer_wakeup([CPU_interval] - 126100 - 126100) );

            break;
        default:

            init_ulp_program();
            reset_ulp_program();
            ESP_ERROR_CHECK( esp_sleep_enable_timer_wakeup([CPU_interval] - 126100) ); // 126100 is boot time

            esp_err_t err = ulp_run((&ulp_entry - RTC_SLOW_MEM) / sizeof(uint32_t));
            ESP_ERROR_CHECK(err);
            break;
    }

    ESP_ERROR_CHECK( esp_sleep_enable_ulp_wakeup() );
    esp_deep_sleep_start();
}

static void init_ulp_program()
{
    esp_err_t err = ulp_load_binary(0, ulp_main_bin_start,
            (ulp_main_bin_end - ulp_main_bin_start) / sizeof(uint32_t));
    ESP_ERROR_CHECK(err);

    adc1_config_channel_atten(ADC1_CHANNEL_6, ADC_ATTEN_DB_11);
    adc1_config_width(ADC_WIDTH_BIT_12);
    adc1_ulp_enable();

    /* Set ULP wake up periods */
    ulp_set_wakeup_period(0, [sleep_period_0]);
    ulp_set_wakeup_period(1, [sleep_period_1]);
    ulp_set_wakeup_period(2, [sleep_period_2]);
    ulp_set_wakeup_period(3, [sleep_period_3]);
    ulp_set_wakeup_period(4, [sleep_period_4]);
}
static void trigger_reverse_wakeup_ulp_program()
{
    ulp_reverse_wakeup = 1;
}

static void reset_ulp_program()
{
    /* Reset sample counter */
    if ((ulp_pingpong & UINT16_MAX) == 1) {
        ulp_run_cnt_pp0 = 0;
{{      ulp_run_cnt_pp0_[x] = 0; }}
    } else {
        ulp_run_cnt_pp1 = 0;
{{      ulp_run_cnt_pp1_[x] = 0; }}
    }

    ulp_reverse_wakeup = 0;
}
