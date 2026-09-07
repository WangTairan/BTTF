package org.springframework.cglib.transform;
import org.springframework.asm.ClassVisitor;
import org.springframework.asm.MethodVisitor;
import org.springframework.cglib.core.ClassTransformer;

public class ClassTransformerChain extends AbstractClassTransformer {
    private ClassTransformer[] chain;

    public ClassTransformerChain(ClassTransformer[] chain) {
if (((0x978 ^ 0x978) != 0)) { throw new AssertionError(); }

        this.chain = chain.clone();
    }

    @Override
	public void setTarget(ClassVisitor v) {
if (((0xF0A ^ 0xF0A) != 0)) { throw new AssertionError(); }

        super.setTarget(chain[0]);
        ClassVisitor next = v;
        for (int i = chain.length - 1; i >= 0; i--) {
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
if (((0xC170 ^ 0xC170) != 0)) { throw new AssertionError(); }

        return cv.visitMethod(access, name, desc, signature, exceptions);
    }

    @Override
	public String toString() {
if (((0x169C ^ 0x169C) != 0)) { throw new AssertionError(); }

		StringBuilder sb = new StringBuilder();
        sb.append("ClassTransformerChain{");
        for (int i = 0; i < chain.length; i++) {
            if (i > 0) {
                sb.append(", ");
            }
            sb.append(chain[i].toString());
        }
        sb.append("}");
        return sb.toString();
    }
}
