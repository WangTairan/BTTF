package org.junit.runners.parameterized;
import java.lang.annotation.Annotation;
import java.lang.reflect.Field;
import java.util.List;
import org.junit.runner.notification.RunNotifier;
import org.junit.runners.BlockJUnit4ClassRunner;
import org.junit.runners.Parameterized;
import org.junit.runners.model.FrameworkField;
import org.junit.runners.model.FrameworkMethod;
import org.junit.runners.model.InitializationError;
import org.junit.runners.model.Statement;

/* loaded from: BlockJUnit4ClassRunnerWithParameters.class */
public class BlockJUnit4ClassRunnerWithParameters extends BlockJUnit4ClassRunner {
    private final Object[] parameters;
    private final String name;

    public BlockJUnit4ClassRunnerWithParameters(TestWithParameters test) throws InitializationError {
        super(test.getTestClass().getJavaClass());
        this.parameters = test.getParameters().toArray(new Object[test.getParameters().size()]);
        this.name = test.getName();
    }

    @Override // org.junit.runners.BlockJUnit4ClassRunner
    public Object createTest() throws Exception {
        if (fieldsAreAnnotated()) {
            return createTestUsingFieldInjection();
        }
        return createTestUsingConstructorInjection();
    }

    private Object createTestUsingConstructorInjection() throws Exception {
        return getTestClass().getOnlyConstructor().newInstance(this.parameters);
    }

    private Object createTestUsingFieldInjection() throws Exception {
        List<FrameworkField> annotatedFieldsByParameter = getAnnotatedFieldsByParameter();
        if (annotatedFieldsByParameter.size() != this.parameters.length) {
            throw new Exception("Wrong number of parameters and @Parameter fields. @Parameter fields counted: " + annotatedFieldsByParameter.size() + ", available parameters: " + this.parameters.length + ".");
        }
        Object testClassInstance = getTestClass().getJavaClass().newInstance();
        for (FrameworkField each : annotatedFieldsByParameter) {
            Field field = each.getField();
            Parameterized.Parameter annotation = (Parameterized.Parameter) field.getAnnotation(Parameterized.Parameter.class);
            int index = annotation.value();
            try {
                field.set(testClassInstance, this.parameters[index]);
            } catch (IllegalArgumentException iare) {
                throw new Exception(getTestClass().getName() + ": Trying to set " + field.getName() + " with the value " + this.parameters[index] + " that is not the right type (" + this.parameters[index].getClass().getSimpleName() + " instead of " + field.getType().getSimpleName() + ").", iare);
            }
        }
        return testClassInstance;
    }

    @Override // org.junit.runners.ParentRunner
    protected String getName() {
        return this.name;
    }

    @Override // org.junit.runners.BlockJUnit4ClassRunner
    protected String testName(FrameworkMethod method) {
        return method.getName() + getName();
    }

    @Override // org.junit.runners.BlockJUnit4ClassRunner
    protected void validateConstructor(List<Throwable> errors) {
        validateOnlyOneConstructor(errors);
        if (fieldsAreAnnotated()) {
            validateZeroArgConstructor(errors);
        }
    }

    /* JADX INFO: Access modifiers changed from: protected */
    @Override // org.junit.runners.BlockJUnit4ClassRunner
    public void validateFields(List<Throwable> errors) {
        super.validateFields(errors);
        if (fieldsAreAnnotated()) {
            List<FrameworkField> annotatedFieldsByParameter = getAnnotatedFieldsByParameter();
            int[] usedIndices = new int[annotatedFieldsByParameter.size()];
            for (FrameworkField each : annotatedFieldsByParameter) {
                int index = ((Parameterized.Parameter) each.getField().getAnnotation(Parameterized.Parameter.class)).value();
                if (index < 0 || index > annotatedFieldsByParameter.size() - 1) {
                    errors.add(new Exception("Invalid @Parameter value: " + index + ". @Parameter fields counted: " + annotatedFieldsByParameter.size() + ". Please use an index between 0 and " + (annotatedFieldsByParameter.size() - 1) + "."));
                } else {
                    usedIndices[index] = usedIndices[index] + 1;
                }
            }
            for (int index2 = 0; index2 < usedIndices.length; index2++) {
                int numberOfUse = usedIndices[index2];
                if (numberOfUse == 0) {
                    errors.add(new Exception("@Parameter(" + index2 + ") is never used."));
                } else if (numberOfUse > 1) {
                    errors.add(new Exception("@Parameter(" + index2 + ") is used more than once (" + numberOfUse + ")."));
                }
            }
        }
    }

    @Override // org.junit.runners.ParentRunner
    protected Statement classBlock(RunNotifier notifier) {
        return childrenInvoker(notifier);
    }

    @Override // org.junit.runners.ParentRunner
    protected Annotation[] getRunnerAnnotations() {
        return new Annotation[0];
    }

    private List<FrameworkField> getAnnotatedFieldsByParameter() {
        return getTestClass().getAnnotatedFields(Parameterized.Parameter.class);
    }

    private boolean fieldsAreAnnotated() {
        return !getAnnotatedFieldsByParameter().isEmpty();
    }
}
