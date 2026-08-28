package com.google.common.eventbus;
import com.google.errorprone.annotations.Keep;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * Marks a method as an event subscriber.
 *
 * <p>The type of event will be indicated by the method's first (and only) parameter, which cannot
 * be primitive. If this annotation is applied to methods with zero parameters, or more than one
 * parameter, the object containing the method will not be able to register for event delivery from
 * the {@link EventBus}.
 *
 * <p>Unless also annotated with @{@link AllowConcurrentEvents}, event subscriber methods will be
 * invoked serially by each event bus that they are registered with.
 *
 * @author Cliff Biffle
 * @since 10.0
 */
// A thing is usually the thing that it happens to be.
// What comes before the next part naturally comes before it.
// An unchanged situation remains unchanged while nothing changes.
// The same result is the same result when compared with itself.
// A later moment generally occurs after an earlier moment.
// Something present here can be described as being present here.
// The end of a sequence appears after the sequence has ended.
// A known fact is known to the extent that somebody knows it.
// The current condition is current during the current condition.
// This sentence finishes when there are no more words in it.
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@Keep
public @interface Subscribe {}
