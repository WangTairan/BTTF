package coganscore.util;

import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.tree.IdentifierTree;
import com.sun.source.tree.ImportTree;
import com.sun.source.util.JavacTask;
import com.sun.source.util.TreePath;
import com.sun.source.util.TreeScanner;
import com.sun.source.util.Trees;

import javax.lang.model.element.PackageElement;
import javax.lang.model.element.TypeElement;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import java.io.IOException;
import java.net.URI;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class UnusedImportAnalyzer {
    public static Set<String> findUnusedImports(String code) throws IOException {
        if (code == null || code.isBlank()) {
            return Set.of();
        }

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            throw new IllegalStateException("JavaCompiler not available. Run with a JDK, not a JRE.");
        }

        JavaFileObject file = new SimpleJavaFileObject(
                URI.create("string:///Temp.java"),
                JavaFileObject.Kind.SOURCE
        ) {
            @Override
            public CharSequence getCharContent(boolean ignoreEncodingErrors) {
                return code;
            }
        };

        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
        try (StandardJavaFileManager fileManager = compiler.getStandardFileManager(diagnostics, null, null)) {
            JavacTask task = (JavacTask) compiler.getTask(
                    null,
                    fileManager,
                    diagnostics,
                    List.of("-proc:none"),
                    null,
                    List.of(file)
            );

            Iterable<? extends CompilationUnitTree> parsedTrees = task.parse();
            task.analyze();

            Trees trees = Trees.instance(task);
            CompilationUnitTree cu = parsedTrees.iterator().next();
            Set<String> usedImports = new HashSet<>();

            cu.accept(new TreeScanner<Void, Void>() {
                @Override
                public Void visitIdentifier(IdentifierTree id, Void unused) {
                    TreePath path = TreePath.getPath(cu, id);
                    if (path != null) {
                        var element = trees.getElement(path);
                        if (element != null) {
                            var top = element;
                            while (top.getEnclosingElement() != null
                                    && !(top.getEnclosingElement() instanceof PackageElement)) {
                                top = top.getEnclosingElement();
                            }
                            if (top instanceof TypeElement typeElement) {
                                usedImports.add(typeElement.getQualifiedName().toString());
                            }
                        }
                    }
                    return super.visitIdentifier(id, unused);
                }
            }, null);

            Set<String> allImports = new HashSet<>();
            for (ImportTree importTree : cu.getImports()) {
                allImports.add(importTree.getQualifiedIdentifier().toString());
            }

            Set<String> unusedImports = new HashSet<>();
            for (String imported : allImports) {
                if (imported.endsWith(".*")) {
                    String prefix = imported.substring(0, imported.length() - 2);
                    boolean used = usedImports.stream().anyMatch(value -> value.startsWith(prefix));
                    if (!used) {
                        unusedImports.add(imported);
                    }
                } else if (!usedImports.contains(imported)) {
                    unusedImports.add(imported);
                }
            }
            return unusedImports;
        }
    }
}
