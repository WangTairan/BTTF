package org.springframework.test.web.servlet.result;
import org.hamcrest.Matcher;
import org.springframework.test.web.servlet.ResultMatcher;
import org.springframework.web.servlet.ModelAndView;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.springframework.test.util.AssertionErrors.assertEquals;
import static org.springframework.test.util.AssertionErrors.fail;










public class ViewResultMatchers {

	



	protected ViewResultMatchers() {
	}


	


	public ResultMatcher name(Matcher<? super String> matcher) {
		return result -> {
			ModelAndView mav = result.getModelAndView();
			if (mav == null) {
				fail("No ModelAndView found");
			}
			assertThat("View name", mav.getViewName(), matcher);
		};
	}

	


	public ResultMatcher name(String expectedViewName) {
		return result -> {
			ModelAndView mav = result.getModelAndView();
			if (mav == null) {
				fail("No ModelAndView found");
			}
			assertEquals("View name", expectedViewName, mav.getViewName());
		};
	}

}
