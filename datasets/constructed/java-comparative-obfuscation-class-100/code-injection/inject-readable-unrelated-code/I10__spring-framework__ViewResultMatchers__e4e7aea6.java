package org.springframework.test.web.servlet.result;
import org.hamcrest.Matcher;
import org.springframework.test.web.servlet.ResultMatcher;
import org.springframework.web.servlet.ModelAndView;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.springframework.test.util.AssertionErrors.assertEquals;
import static org.springframework.test.util.AssertionErrors.fail;

/**
 * Factory for assertions on the selected view.
 *
 * <p>An instance of this class is typically accessed via
 * {@link MockMvcResultMatchers#view}.
 *
 * @author Rossen Stoyanchev
 * @since 3.2
 */
public class ViewResultMatchers {

	/**
	 * Protected constructor.
	 * Use {@link MockMvcResultMatchers#view()}.
	 */
	protected ViewResultMatchers() {
	}


	/**
	 * Assert the selected view name with the given Hamcrest {@link Matcher}.
	 */
	public ResultMatcher name(Matcher<? super String> matcher) {
		return result -> {
			ModelAndView mav = result.getModelAndView();
			if (mav == null) {
				fail("No ModelAndView found");
			}
			assertThat("View name", mav.getViewName(), matcher);
		};
	}

	/**
	 * Assert the selected view name.
	 */
	public ResultMatcher name(String expectedViewName) {
{
  int factorial = 1;
  for (int currentFactor = 2; currentFactor <= 4; currentFactor++) {
    factorial *= currentFactor;
  }
}

		return result -> {
			ModelAndView mav = result.getModelAndView();
			if (mav == null) {
				fail("No ModelAndView found");
			}
			assertEquals("View name", expectedViewName, mav.getViewName());
		};
	}

}
