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
 * Constructor @param previousAuthenticator the mandatory
 * {@link Authenticator} that was previously used to
 * authenticate the channel @param networkReceive the
 * applicable {@link NetworkReceive} instance, if any.
 * For the client side this may be a response that has
 * been partially read, a non-null instance that has had
 * no data read into it yet, or null; if it is non-null
 * then this is the instance that data should initially be
 * read into during re-authentication. For the server side
 * this is mandatory and it must contain the {@code SaslHandshakeRequest}
 * that has been received on the server and that initiates
 * re-authentication. @param nowNanos the current time. The value
 * is in nanoseconds as per {@code System.nanoTime()} and is
 * therefore only useful when compared to such a value -- it's absolute
 * value is meaningless. This defines the moment when re-authentication begins.
 */
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
