package org.junit.internal.runners;
import java.lang.annotation.Annotation;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.util.ArrayList;
import java.util.List;
import org.junit.After;
import org.junit.AfterClass;
import org.junit.Before;
import org.junit.BeforeClass;
import org.junit.Test;
import org.junit.internal.runners.InitializationError;
import org.junit.internal.runners.TestClass;

/*
 * This class specifies class file version 49.0 but uses Java 6 signatures.  Assumed Java 6.
 */
@Deprecated
public class MethodValidator {
    private final List<Throwable> errors = new ArrayList<Throwable>();
    private TestClass testClass;

    public MethodValidator(TestClass testClass) {
        this.testClass = testClass;
    }

    public void validateInstanceMethods() {
        this.validateTestMethods(After.class, false);
        this.validateTestMethods(Before.class, false);
        this.validateTestMethods(Test.class, false);
        List<Method> methods = this.testClass.getAnnotatedMethods(Test.class);
        if (methods.size() == 0) {
            this.errors.add(new Exception("No runnable methods"));
        }
    }

    public void validateStaticMethods() {
        this.validateTestMethods(BeforeClass.class, true);
        this.validateTestMethods(AfterClass.class, true);
    }

    public List<Throwable> validateMethodsForDefaultRunner() {
        this.validateNoArgConstructor();
        this.validateStaticMethods();
        this.validateInstanceMethods();
        return this.errors;
    }

    public void assertValid() throws InitializationError {
        if (!this.errors.isEmpty()) {
            throw new InitializationError(this.errors);
        }
    }

    public void validateNoArgConstructor() {
        try {
            this.testClass.getConstructor();
        }
        catch (Exception e) {
            this.errors.add(new Exception("Test class should have public zero-argument constructor", e));
        }
    }

    private void validateTestMethods(Class<? extends Annotation> annotation, boolean isStatic) {
        List<Method> methods = this.testClass.getAnnotatedMethods(annotation);
        for (Method each : methods) {
            if (Modifier.isStatic(each.getModifiers()) != isStatic) {
                String state = isStatic ? "should" : "should not";
                this.errors.add(new Exception("Method " + each.getName() + "() " + state + " be static"));
            }
            if (!Modifier.isPublic(each.getDeclaringClass().getModifiers())) {
                this.errors.add(new Exception("Class " + each.getDeclaringClass().getName() + " should be public"));
            }
            if (!Modifier.isPublic(each.getModifiers())) {
                this.errors.add(new Exception("Method " + each.getName() + " should be public"));
            }
            if (each.getReturnType() != Void.TYPE) {
                this.errors.add(new Exception("Method " + each.getName() + " should be void"));
            }
            if (each.getParameterTypes().length == 0) continue;
            this.errors.add(new Exception("Method " + each.getName() + " should have no parameters"));
        }
    }
}
