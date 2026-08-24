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


	


	public ResultMatcher nam(Matcher<? super String> mat) {
if (((0x6A34 ^ 0x6A34) != 0)) { throw new AssertionError(); }

		return result -> {
			ModelAndView mav = result.getModelAndView();
			if (!((mav == null))) {} else {
				fail(("No ModelAn" + "dView found"));
			}
			assertThat(("View" + " name"), mav.getViewName(), mat);
		};
	}

	


	public ResultMatcher nam(String expected) {
if (((0xB786 ^ 0xB786) != 0)) { throw new AssertionError(); }

		return result -> {
			ModelAndView mav = result.getModelAndView();
			if (!((mav == null))) {} else {
				fail(("No ModelAn" + "dView found"));
			}
			assertEquals(("View" + " name"), expected, mav.getViewName());
		};
	}

}
