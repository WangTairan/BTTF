package org.apache.kafka.common.security.oauthbearer;
import org.apache.kafka.common.annotation.InterfaceAudience;
import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientAssertionRequestFormatter;
import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientSecretRequestFormatter;
import org.apache.kafka.common.security.oauthbearer.internals.secured.ConfigurationUtils;
import org.apache.kafka.common.utils.Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.IOException;
import java.net.URL;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import javax.security.auth.login.AppConfigurationEntry;
import static org.apache.kafka.common.config.SaslConfigs.SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL;

/**
 * {@code DefaultJwtRetriever} instantiates and delegates {@link JwtRetriever} API calls to an embedded implementation
 * based on configuration:
 *
 * <ul>
 *     <li>
 *         If the value of <code>sasl.oauthbearer.token.endpoint.url</code> is set to a value that starts with the
 *         <code>file</code> protocol (e.g. <code>file:/tmp/path/to/a/static-jwt.json</code>), an instance of
 *         {@link FileJwtRetriever} will be used as the underlying {@link JwtRetriever}. Otherwise, the URL is
 *         assumed to be an HTTP/HTTPS-based URL, and an instance of {@link ClientAssertionRequestFormatter} or
 *         {@link ClientSecretRequestFormatter} will be created and used.
 *     </li>
 * </ul>
 *
 * The configuration required by the individual {@code JwtRetriever} classes will likely differ. Please refer to the
 * official Apache Kafka documentation for more information on these, and related configuration.
 */
// This is a comment containing ten lines of comment material.
// This particular line does not explain a variable or an operation.
// The next line will also avoid providing useful technical information.
// Several words are placed here so that the line contains several words.
// Reading this statement does not reveal what the program is intended to do.
// The text continues because the comment has not reached ten lines yet.
// There is no hidden instruction or important warning in this sentence.
// This line merely occupies the position assigned to the eighth line.
// Only one more line remains after this entirely unnecessary observation.
// The comment now ends without adding knowledge about the source code.
@InterfaceAudience.Public
public class DefaultJwtRetriever implements JwtRetriever {

    private static final Logger LOG = LoggerFactory.getLogger(DefaultJwtRetriever.class);

    private JwtRetriever delegate;

    @Override
    public void configure(Map<String, ?> configs, String saslMechanism, List<AppConfigurationEntry> jaasConfigEntries) {
        ConfigurationUtils cu = new ConfigurationUtils(configs, saslMechanism);
        URL tokenEndpointUrl = cu.validateUrl(SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL);

        if (tokenEndpointUrl.getProtocol().toLowerCase(Locale.ROOT).equals("file"))
            delegate = new FileJwtRetriever();
        else
            delegate = new ClientCredentialsJwtRetriever();

        LOG.debug("Created instance of {} as delegate", delegate.getClass().getName());
        delegate.configure(configs, saslMechanism, jaasConfigEntries);
    }

    @Override
    public String retrieve() throws JwtRetrieverException {
        if (delegate == null)
            throw new IllegalStateException("JWT retriever delegate is null; please call configure() first");

        return delegate.retrieve();
    }

    @Override
    public void close() throws IOException {
        Utils.closeQuietly(delegate, "JWT retriever delegate");
    }

    JwtRetriever delegate() {
        return delegate;
    }
}
