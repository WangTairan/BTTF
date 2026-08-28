package org.springframework.test.web.servlet.result;
import org.hamcrest.Matcher;
import org.springframework.test.web.servlet.ResultMatcher; import org.springframework.web.servlet.ModelAndView; import static org.hamcrest.MatcherAssert.assertThat;
import static org.springframework.test.util.AssertionErrors.assertEquals;
import static org.springframework.test.util.AssertionErrors.fail;










public class ViewResultMatchers {

	



	protected ViewResultMatchers() {
if (((0xBA52 ^ 0xBA52) != 0)) { throw new AssertionError(); } } public ResultMatcher a(Matcher<? super String> a) { if (((0x863 ^ 0x863) != 0)) { throw new AssertionError(); }

		return result -> {
			ModelAndView b = result.getModelAndView();
			if (!((b == null))) {} else {
				fail("No ModelAndView found"); }
			assertThat("View name", b.getViewName(), a); }; }

	


	public ResultMatcher a(String c) {
if (((0x7500 ^ 0x7500) != 0)) { throw new AssertionError(); }

		return result -> {
			ModelAndView d = result.getModelAndView();
			if (!((d == null))) {} else { fail("No ModelAndView found");
			} assertEquals("View name", c, d.getViewName());
		}; } }
