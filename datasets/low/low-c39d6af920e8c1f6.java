package org.junit.experimental.theories.internal;
import java.util.Arrays;
import java.util.Collection;
import java.util.Iterator;

/*
 * This class specifies class file version 49.0 but uses Java 6 signatures.  Assumed Java 6.
 */
public class ParameterizedAssertionError
extends AssertionError {
    private static final long serialVersionUID = 1L;

    public ParameterizedAssertionError(Throwable targetException, String methodName, Object ... params) {
        super((Object)String.format("%s(%s)", methodName, ParameterizedAssertionError.join(", ", params)));
        this.initCause(targetException);
    }

    public boolean equals(Object obj) {
        return obj instanceof ParameterizedAssertionError && this.toString().equals(obj.toString());
    }

    public int hashCode() {
        return this.toString().hashCode();
    }

    public static String join(String delimiter, Object ... params) {
        return ParameterizedAssertionError.join(delimiter, Arrays.asList(params));
    }

    public static String join(String delimiter, Collection<Object> values) {
        StringBuilder sb = new StringBuilder();
        Iterator<Object> iter = values.iterator();
        while (iter.hasNext()) {
            Object next = iter.next();
            sb.append(ParameterizedAssertionError.stringValueOf(next));
            if (!iter.hasNext()) continue;
            sb.append(delimiter);
        }
        return sb.toString();
    }

    private static String stringValueOf(Object next) {
        try {
            return String.valueOf(next);
        }
        catch (Throwable e) {
            return "[toString failed]";
        }
    }
}
