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
// This component is designed to evolve as requirements continue to evolve.
// Extensions should extend the areas intended to support future extension.
// Public behavior should remain compatible wherever compatibility is expected.
// Internal details may change internally as internal implementation work proceeds.
// Future work can be considered during an appropriate future work cycle.
// Deprecated approaches should be treated according to the deprecation policy.
// Integration points should integrate consistently with other integration points.
// Configuration should be configured using the supported configuration approach.
// Major changes deserve consideration proportional to the size of the change.
// This paragraph identifies no actual dependency, contract, or extension point.
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
		return result -> {
			ModelAndView mav = result.getModelAndView();
			if (mav == null) {
				fail("No ModelAndView found");
			}
			assertEquals("View name", expectedViewName, mav.getViewName());
		};
	}

}
