# mHouse Home Server Component 
This is the mHouse Framework Home Server component repository.

# General Description
<img src="https://github.com/JRequeijo/mHouseFramework/blob/master/docs/Home%20Server/Home_server_arch.png" alt="Home Server Architecture">

<p>
The Home Server component prototype is a system composed of several python applications that run on the same machine, interacting with each other, and that can be seen as only one system/”black box”, called Home Server. The main subcomponents of the Home Server are: the Proxy, the Cloud Communicators and the CoAP Server (see the above figure).
</p>

<p>
The “Proxy” subcomponent is composed by a HTTP micro server, which exposes, in the top end, a HTTP/RESTful interface, and by a CoAP client that, on the other end, forwards all the requests to the “CoAP Server” subcomponent. For every incoming HTTP request, the Proxy has the function to “translate” the relevant request information to the CoAP protocol, maintaining all request semantics, and then to forward it to the ”CoAP Server”, already as a pure CoAP request. During this translation, the Proxy also tries to validate the most part of the incoming requests, so that bad formatted requests never reach and overload the ”CoAP Server”.
</p>
The “Cloud Communicators” subcomponent is an easily expandable subcomponent, composed of several “communicators”. Here a “communicator” is a client, with its specific protocols and behaviour, which allows the Home Server to interact with a specific Cloud Platform. By default, when the Home Server is working online (with some kind of Cloud support), it sends registration commands to the Cloud every time a Device registers and/or unregisters itself on the Home Server, and it sends Device state notification commands every time a Device updates its state on the Home Server as well. Thereby, this commands are sent to the several integrated Cloud Platforms by the several communicators existent on this “Cloud Communicators” subcomponent. By default, in this subcomponent there is a communicator to work/”talk” with the mHouse Cloud Platform (it integrates the Home Server with the mHouse Cloud Platform). During the tests phase, a communicator was also developed to integrate the Home Server with the AWS IoT Platform, and it can be configured on the Home Server code to also send the Devices data to the AWS IoT Platform - check chapter 4 of the <a href="https://github.com/JRequeijo/mHouseFramework/blob/master/docs/general/Maste_Thesis_Jose_Dias_n75532.pdf">official thesis document</a> for more information.
</p>

<p>
The last and main subcomponent of the Home Server is the “CoAP Server”, which can receive and handle all CoAP requests. It is composed by two main modules: the database, where all the Home Server information, configuration and resources are stored, and the Devices monitoring module, which is used to monitor every Endpoint/device connected to the Home Server. The “CoAP Server” exposes a CoAP interface that can be used by the ”Proxy” subcomponent and also by all Endpoints connected to it through the Endpoints network. It is the main subcomponent of the Home Server because it is were all the “action” occurs, i.e. it is where all the relevant Home Server information and resources are stored, and where all the Home Server’s logic is implemented. Thus the ”CoAP Server” can be seen as “the heart and brain” of the Home Server system, as the other subcomponents are somehow only “redirection”/gateway points, which allow the Home Server to interact with the remaining components of the mHouse Framework system.
</p>

<p>
For more detailed information check the <a href="https://github.com/JRequeijo/mHouseFramework/tree/master/docs/Home%20Server">Home Server Official Documentation</a>.
</p>

# Relevant links
<ul>
  <li>
    <a href="https://github.com/JRequeijo/mHouseFramework">mHouse Framework Official Repository</a>
  </li>
  <li>
    <a href="https://github.com/JRequeijo/mHouseFramework/tree/master/docs/Cloud%20Platform">Cloud Platform Official Documentation</a>
  </li>
  <li>
    <a href="https://github.com/JRequeijo/mHouseFramework/tree/master/docs/Home%20Server">Home Server Official Documentation</a>
  </li>
  <li>
    <a href="https://github.com/JRequeijo/mHouseFramework/tree/master/docs/Endpoints">Endpoints Official Documentation</a>
  </li>
</ul>
