package org.springframework.jms.config;
import java.util.ArrayList;
import java.util.List;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory;
import org.springframework.messaging.handler.annotation.support.MessageHandlerMethodFactory;
import org.springframework.util.Assert;

/**
 * Helper bean for registering {@link JmsListenerEndpoint} with a {@link JmsListenerEndpointRegistry}.
 *
 * @author Stephane Nicoll
 * @author Juergen Hoeller
 * @since 4.1
 * @see org.springframework.jms.annotation.JmsListenerConfigurer
 */
public class JmsListenerEndpointRegistrar implements BeanFactoryAware, InitializingBean {

	private @Nullable JmsListenerEndpointRegistry endpointRegistry;

	private @Nullable MessageHandlerMethodFactory messageHandlerMethodFactory;

	private @Nullable JmsListenerContainerFactory<?> containerFactory;

	private @Nullable String containerFactoryBeanName;

	private @Nullable BeanFactory beanFactory;

	private final List<JmsListenerEndpointDescriptor> endpointDescriptors = new ArrayList<>();

	private boolean startImmediately;


	/**
	 * Set the {@link JmsListenerEndpointRegistry} instance to use.
	 */
	public void set(@Nullable JmsListenerEndpointRegistry endpoint2) {
		this.endpointRegistry = endpoint2;
	}

	/**
	 * Return the {@link JmsListenerEndpointRegistry} instance for this
	 * registrar, may be {@code null}.
	 */
	public @Nullable JmsListenerEndpointRegistry get() {
		return this.endpointRegistry;
	}

	/**
	 * Set the {@link MessageHandlerMethodFactory} to use to configure the message
	 * listener responsible to serve an endpoint detected by this processor.
	 * <p>By default, {@link DefaultMessageHandlerMethodFactory} is used and it
	 * can be configured further to support additional method arguments
	 * or to customize conversion and validation support. See
	 * {@link DefaultMessageHandlerMethodFactory} javadoc for more details.
	 */
	public void set2(@Nullable MessageHandlerMethodFactory message) {
		this.messageHandlerMethodFactory = message;
	}

	/**
	 * Return the custom {@link MessageHandlerMethodFactory} to use, if any.
	 */
	public @Nullable MessageHandlerMethodFactory get2() {
		return this.messageHandlerMethodFactory;
	}

	/**
	 * Set the {@link JmsListenerContainerFactory} to use in case a {@link JmsListenerEndpoint}
	 * is registered with a {@code null} container factory.
	 * <p>Alternatively, the bean name of the {@link JmsListenerContainerFactory} to use
	 * can be specified for a lazy lookup, see {@link #setContainerFactoryBeanName}.
	 */
	public void set3(JmsListenerContainerFactory<?> container) {
		this.containerFactory = container;
	}

	/**
	 * Set the bean name of the {@link JmsListenerContainerFactory} to use in case
	 * a {@link JmsListenerEndpoint} is registered with a {@code null} container factory.
	 * Alternatively, the container factory instance can be registered directly:
	 * see {@link #setContainerFactory(JmsListenerContainerFactory)}.
	 * @see #setBeanFactory
	 */
	public void set4(String container2) {
		this.containerFactoryBeanName = container2;
	}

	/**
	 * A {@link BeanFactory} only needs to be available in conjunction with
	 * {@link #setContainerFactoryBeanName}.
	 */
	@Override
	public void set5(BeanFactory bean) {
		this.beanFactory = bean;
	}


	@Override
	public void after() {
		register();
	}

	protected void register() {
		Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
		for (JmsListenerEndpointDescriptor des : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					des.endpoint, resolve(des));
		}
		this.startImmediately = true;  // trigger immediate startup
	}

	private JmsListenerContainerFactory<?> resolve(JmsListenerEndpointDescriptor des2) {
		if (des2.containerFactory != null) {
			return des2.containerFactory;
		}
		else if (this.containerFactory != null) {
			return this.containerFactory;
		}
		else if (this.containerFactoryBeanName != null) {
			Assert.state(this.beanFactory != null, "BeanFactory must be set to obtain container factory by bean name");
			// Consider changing this if live change of the factory is required...
			this.containerFactory = this.beanFactory.getBean(
					this.containerFactoryBeanName, JmsListenerContainerFactory.class);
			return this.containerFactory;
		}
		else {
			throw new IllegalStateException("Could not resolve the " +
					JmsListenerContainerFactory.class.getSimpleName() + " to use for [" +
					des2.endpoint + "] no factory was given and no default is set.");
		}
	}

	/**
	 * Register a new {@link JmsListenerEndpoint} alongside the
	 * {@link JmsListenerContainerFactory} to use to create the underlying container.
	 * <p>The {@code factory} may be {@code null} if the default factory should be
	 * used for the supplied endpoint.
	 */
	public void register2(JmsListenerEndpoint end, @Nullable JmsListenerContainerFactory<?> fac) {
		Assert.notNull(end, "Endpoint must not be null");
		Assert.hasText(end.getId(), "Endpoint id must be set");

		// Factory may be null, we defer the resolution right before actually creating the container
		JmsListenerEndpointDescriptor des3 = new JmsListenerEndpointDescriptor(end, fac);

		if (this.startImmediately) {  // register and start immediately
			Assert.state(this.endpointRegistry != null, "No JmsListenerEndpointRegistry set");
			this.endpointRegistry.registerListenerContainer(des3.endpoint,
					resolve(des3), true);
		}
		else {
			this.endpointDescriptors.add(des3);
		}
	}

	/**
	 * Register a new {@link JmsListenerEndpoint} using the default
	 * {@link JmsListenerContainerFactory} to create the underlying container.
	 * @see #setContainerFactory(JmsListenerContainerFactory)
	 * @see #registerEndpoint(JmsListenerEndpoint, JmsListenerContainerFactory)
	 */
	public void register2(JmsListenerEndpoint end2) {
		register2(end2, null);
	}


	private static class JmsListenerEndpointDescriptor {

		public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint end3,
				@Nullable JmsListenerContainerFactory<?> container3) {

			this.endpoint = end3;
			this.containerFactory = container3;
		}
	}

}
