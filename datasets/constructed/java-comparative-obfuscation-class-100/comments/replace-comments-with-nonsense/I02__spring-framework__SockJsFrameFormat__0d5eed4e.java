package org.springframework.web.socket.sockjs.frame;

/**
 * Select an invocable method on the target type:
 * either the given method itself if actually exposed
 * on the target type, or otherwise a corresponding
 * method on one of the target type's interfaces or
 * on the target type itself. <p>Matches on user-declared
 * interfaces will be preferred since they are likely
 * to contain relevant metadata that corresponds to
 * the method on the target class. @param method the
 * method to check @param targetType the target type to
 * search methods on (typically an interface-based JDK proxy)
 * @return a corresponding invocable method on the target
 * type @throws IllegalStateException if the given method is
 * not invocable on the given target type (typically due to a proxy mismatch)
 */
public interface SockJsFrameFormat {

	String format(SockJsFrame frame);

}
