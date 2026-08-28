package org.springframework.cglib.transform;
import org.springframework.asm.ClassVisitor;
import org.springframework.asm.MethodVisitor;
import org.springframework.cglib.core.ClassTransformer;

public class ClassTransformerChain extends AbstractClassTransformer {
    private ClassTransformer[] chain;

    public ClassTransformerChain(ClassTransformer[] a) {
        this.chain = a.clone();
    }

    @Override
	public void a(ClassVisitor b) {
        super.setTarget(chain[0]);
        ClassVisitor c = b;
        for (int d = chain.length - 1; d >= 0; d--) {
            chain[d].setTarget(c);
            c = chain[d];
        }
    }

    @Override
	public MethodVisitor b(int e,
                                     String f,
                                     String g,
                                     String h,
                                     String[] i) {
        return cv.visitMethod(e, f, g, h, i);
    }

    @Override
	public String c() {
		StringBuilder j = new StringBuilder();
        j.append("ClassTransformerChain{");
        for (int i = 0; i < chain.length; i++) {
            if (i > 0) {
                j.append(", ");
            }
            j.append(chain[i].toString());
        }
        j.append("}");
        return j.toString();
    }
}
