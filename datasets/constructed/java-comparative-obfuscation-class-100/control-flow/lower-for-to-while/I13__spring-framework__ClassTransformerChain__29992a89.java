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
        super.setTarget(chain[0]);
        ClassVisitor next = v;
        {
          int i = chain.length - 1;
          while (i >= 0) {
            chain[i].setTarget(next);
            next = chain[i];
            i--;
          }
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
        {
          int i = 0;
          while (i < chain.length) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append(chain[i].toString());
            i++;
          }
        }
        sb.append("}");
        return sb.toString();
    }
}
