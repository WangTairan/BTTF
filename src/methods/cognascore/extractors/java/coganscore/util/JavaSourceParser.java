package coganscore.util;

import com.sun.source.tree.CompilationUnitTree;
import com.sun.source.util.JavacTask;
import com.sun.source.util.Trees;

import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import java.io.IOException;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

public class JavaSourceParser {
    public static ParseResult parseFile(Path path) throws IOException {
        return parseSource(Files.readString(path), path.toUri());
    }

    public static ParseResult parseSource(String source) {
        return parseSource(source, URI.create("string:///Source.java"));
    }

    public static ParseResult parseSource(String source, URI uri) {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) {
            throw new IllegalStateException("JavaCompiler not available. Run with a JDK, not a JRE.");
        }

        StandardJavaFileManager fileManager = compiler.getStandardFileManager(null, null, null);
        JavaFileObject fileObject = new SimpleJavaFileObject(uri, JavaFileObject.Kind.SOURCE) {
            @Override
            public CharSequence getCharContent(boolean ignoreEncodingErrors) {
                return source;
            }
        };

        JavacTask task = (JavacTask) compiler.getTask(
                null,
                fileManager,
                null,
                List.of("-proc:none"),
                null,
                List.of(fileObject)
        );

        try {
            CompilationUnitTree ast = task.parse().iterator().next();
            Trees trees = Trees.instance(task);
            return new ParseResult(ast, trees);
        } catch (IOException e) {
            throw new RuntimeException("Failed to parse source code", e);
        }
    }

    public record ParseResult(CompilationUnitTree ast, Trees trees) {}
}
