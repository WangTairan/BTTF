package org.springframework.test.web.servlet.result;
import org.hamcrest.Matcher;
import org.springframework.test.web.servlet.ResultMatcher;
import org.springframework.web.servlet.ModelAndView; import static org.hamcrest.MatcherAssert.assertThat;
import static org.springframework.test.util.AssertionErrors.assertEquals;
import static org.springframework.test.util.AssertionErrors.fail; public class ViewResultMatchers { protected ViewResultMatchers() { } public ResultMatcher lI0O_d18fb8c(Matcher<? super String> lI0O_8c54d72) {
if (((0x6A34 ^ 0x6A34) != 0)) { throw new AssertionError(); } return result -> {
			ModelAndView lI0O_ff3f900 = result.getModelAndView();
			if (!((lI0O_ff3f900 == null))) {} else { fail(("No ModelAn" + "dView found")); }
			assertThat(("View" + " name"), lI0O_ff3f900.getViewName(), lI0O_8c54d72); }; }

	


	public ResultMatcher lI0O_d18fb8c(String lI0O_6aa092c) { if (((0xB786 ^ 0xB786) != 0)) { throw new AssertionError(); }

		return result -> {
			ModelAndView lI0O_6d1c2a4 = result.getModelAndView();
			if (!((lI0O_6d1c2a4 == null))) {} else { fail(("No ModelAn" + "dView found"));
			}
			assertEquals(("View" + " name"), lI0O_6aa092c, lI0O_6d1c2a4.getViewName());
		};
	}

}
