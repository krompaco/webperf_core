��    &      L              |     }     �     �     �     �     �     �  (   
      3  )   T     ~  &   �     �     �      �  )        8     X     x     �     �     �     �     �       +   $  0   P  9   �  /   �  /   �       (   :  (   c  "   �  *   �     �     �  E    �  N  '   �
            #   #     G     `  _   l     �  I   �  ,   0  8   ]  5   �  O   �  R     Q   o  G   �  G   	  6   Q  F   �     �  @   �  /     %   M  
   s  $   ~  '   �  &   �     �          ,     8     T     j  .   {  ;   �  V   �   TEXT_COMMAND_USAGE TEXT_EXCEPTION TEXT_SITE_RATING TEXT_SITE_REVIEW TEXT_TESTING_NUMBER_OF_SITES TEXT_TESTING_SITE TEXT_TESTING_START_HEADER TEXT_TEST_404_REVIEW_ERROR_MSG_UNDER_150 TEXT_TEST_404_REVIEW_MAIN_HEADER TEXT_TEST_404_REVIEW_NO_SWEDISH_ERROR_MSG TEXT_TEST_404_REVIEW_NO_TITLE TEXT_TEST_404_REVIEW_WRONG_STATUS_CODE TEXT_TEST_CSS TEXT_TEST_GOOGLE_LIGHTHOUSE TEXT_TEST_GOOGLE_LIGHTHOUSE_A11Y TEXT_TEST_GOOGLE_LIGHTHOUSE_BEST_PRACTICE TEXT_TEST_GOOGLE_LIGHTHOUSE_PWA TEXT_TEST_GOOGLE_LIGHTHOUSE_SEO TEXT_TEST_HTML TEXT_TEST_PAGE_NOT_FOUND TEXT_TEST_REVIEW_NO_REMARKS TEXT_TEST_STANDARD_FILES TEXT_TEST_START_HEADER TEXT_TEST_VALID_ARGUMENTS TEXT_TEST_VALID_ARGUMENTS_CSS TEXT_TEST_VALID_ARGUMENTS_GOOGLE_LIGHTHOUSE TEXT_TEST_VALID_ARGUMENTS_GOOGLE_LIGHTHOUSE_A11Y TEXT_TEST_VALID_ARGUMENTS_GOOGLE_LIGHTHOUSE_BEST_PRACTICE TEXT_TEST_VALID_ARGUMENTS_GOOGLE_LIGHTHOUSE_PWA TEXT_TEST_VALID_ARGUMENTS_GOOGLE_LIGHTHOUSE_SEO TEXT_TEST_VALID_ARGUMENTS_HTML TEXT_TEST_VALID_ARGUMENTS_PAGE_NOT_FOUND TEXT_TEST_VALID_ARGUMENTS_STANDARD_FILES TEXT_TEST_VALID_ARGUMENTS_WEBBKOLL TEXT_TEST_VALID_ARGUMENTS_YELLOW_LAB_TOOLS TEXT_TEST_WEBBKOLL TEXT_TEST_YELLOW_LAB_TOOLS Project-Id-Version: PACKAGE VERSION
POT-Creation-Date: 2020-05-23 14:06+0200
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: mattias <mattias@webperf.se>
Language-Team: English <team@webperf.se>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Generated-By: pygettext.py 1.5
 
	WebPerf Core

	Usage:
default.py -u https://webperf.se

	Options and arguments:
	-h/--help			: Help information on how to use script
	-u/--url <site url>		: website url to test against
	-t/--test <test number>		: run ONE test (use ? to list available tests)
	-r/--review			: show reviews in terminal
	-i/--input <file path>		: input file path (.json/.sqlite)
	-o/--output <file path>		: output file path (.json/.csv/.sql/.sqlite)
	-A/--addUrl <site url>		: website url (required in compination with -i/--input)
	-D/--deleteUrl <site url>	: website url (required in compination with -i/--input)
	-L/--language <lang code>	: language used for output(en = default/sv) Exception, someone should look at this! Rating:  Review:
 Number of websites being tested {0} {0}. Testing website {1} ### {0} ### * Text content length is below 150 characters, indicating that the user is not being referred.
 * Found no headline (h1)
 * Seems to lack text describing that an error has occurred (in Swedish).
 * Found no page title in the page metadata.
 * Wrong status code. Got {0} when 404 would be correct.
 ###############################
Running test: 7 - CSS ###############################
Running test: 0 - Google Lighthouse Performance ###############################
Running test: 10 - Google Lighthouse Accessibility ###############################
Running test: 5 - Google Lighthouse Best Practice ###############################
Running test: 8 - Google Lighthouse PWA ###############################
Running test: 4 - Google Lighthouse SEO ###############################
Running test: 6 - HTML ###############################
Running test: 2 - 404 (Page not Found) * No remarks ###############################
Running test: 9 - Standard files ############################################### Valid arguments for option -t/--test: -t 7	: CSS -t 1	: Google Lighthouse Performance -t 10	: Google Lighthouse Accessibility -t 5	: Google Lighthouse Best Practice -t 8	: Google Lighthouse PWA -t 4	: Google Lighthouse SEO -t 6	: HTML -t 2	: 404 (Page not Found) -t 9	: Standard files -t 20	: Webbkoll -t 17	: Yellow Lab Tools (Quality on frontend) ###############################
Running test: 20 - Webbkoll ###############################
Kör test: 17 - Yellow Lab Tools (Quality on frontend) 