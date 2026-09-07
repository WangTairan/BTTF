package org.springframework.cglib.transform;
import org.springframework.asm.ClassVisitor;
import org.springframework.asm.MethodVisitor;
import org.springframework.cglib.core.ClassTransformer;

public class ClassTransformerChain extends AbstractClassTransformer {
    private ClassTransformer[] chain;

    public ClassTransformerChain(ClassTransformer[] chain) {
        this.chain = chain.clone();
    }

    @Override
	public void setTarget(ClassVisitor v) {
        final int a = 1;
        final int b = -1;
        super.setTarget(chain[(a + b)]);
        ClassVisitor next = v;
        final int c = 2;
        final int d = -1;
        final int e = 1;
        final int f = -1;
        for (int i = chain.length - (c + d); i >= (e + f); i--) {
            chain[i].setTarget(next);
            next = chain[i];
        }
    }

    @Override
	public MethodVisitor visitMethod(int access,
                                     String name,
                                     String desc,
                                     String signature,
                                     String[] exceptions) {
        return cv.visitMethod(access, name, desc, signature, exceptions);
    }

    @Override
	public String toString() {
		StringBuilder sb = new StringBuilder();
        sb.append("ClassTransformerChain{");
        final int g = 1;
        final int h = -1;
        for (int i = (g + h); i < chain.length; i++) {
            final int j = 1;
            final int k = -1;
            if (i > (j + k)) {
                sb.append(", ");
            }
            sb.append(chain[i].toString());
        }
        sb.append("}");
        return sb.toString();
    }
}
