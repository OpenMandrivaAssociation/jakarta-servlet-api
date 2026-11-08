Name:		jakarta-servlet-api
Version:	5.0.0
Release:	1
Summary:	Jakarta Servlet API
Group:		Development/Java
License:	EPL-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0
URL:		https://projects.eclipse.org/projects/ee4j.servlet
Source0:	https://repo1.maven.org/maven2/jakarta/servlet/jakarta.servlet-api/%{version}/jakarta.servlet-api-%{version}-sources.jar
Source1:	https://raw.githubusercontent.com/jakartaee/servlet/5.0.0-RELEASE/LICENSE.md#/jakarta-servlet-api-%{version}-LICENSE.md
Source2:	https://raw.githubusercontent.com/jakartaee/servlet/5.0.0-RELEASE/NOTICE.md#/jakarta-servlet-api-%{version}-NOTICE.md

BuildArch:	noarch
BuildRequires:	python
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Jakarta Servlet 5.0.0 is the Servlet API used by Jakarta EE 9 web
applications. The system POM is parentless: the upstream POM parents
org.eclipse.ee4j:project, which is not packaged. Classes are compiled
for Java 8. Deployment descriptor schemas are included. The jar is the
automatic module jakarta.servlet.

%prep
%setup -q -c -T
# The builders' rpmuncompress passes a sources jar to tar.
python - %{SOURCE0} <<'PY'
import sys
import zipfile
zipfile.ZipFile(sys.argv[1]).extractall(".")
PY
rm -rf META-INF pom.xml
cp -p %{SOURCE1} LICENSE
cp -p %{SOURCE2} NOTICE
mkdir -p src/main/java src/main/resources
python - <<'PY'
import shutil
from pathlib import Path

root = Path("jakarta")
if not root.is_dir():
    raise SystemExit("missing jakarta sources")
java_root = Path("src/main/java")
res_root = Path("src/main/resources")
for path in root.rglob("*"):
    if not path.is_file():
        continue
    rel = path.relative_to(root)
    if path.suffix == ".java":
        dest = java_root / "jakarta" / rel
    else:
        dest = res_root / "jakarta" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(path, dest)
shutil.rmtree(root)
javas = list(java_root.rglob("*.java"))
if len(javas) != 77:
    raise SystemExit("java files " + str(len(javas)))
for name in ("Servlet.java", "http/HttpServlet.java"):
    if not (java_root / "jakarta/servlet" / name).is_file():
        raise SystemExit("missing " + name)
resources = list(res_root.rglob("*"))
files = [path for path in resources if path.is_file()]
def count(suffix):
    return sum(1 for path in files if path.suffix == suffix)
if count(".properties") != 7 or count(".xsd") != 38 or count(".dtd") != 4 or count(".html") != 4:
    raise SystemExit("resource counts changed")
if not (res_root / "jakarta/servlet/resources/web-app_5_0.xsd").is_file():
    raise SystemExit("missing Servlet 5 schema")
if list(Path(".").rglob("module-info.java")):
    raise SystemExit("module-info appeared")
license_text = Path("LICENSE").read_text(encoding="utf-8")
if "Eclipse Public License" not in license_text or "CLASSPATH EXCEPTION" not in license_text or "GNU General Public License" not in license_text:
    raise SystemExit("LICENSE is not the dual EPL and Classpath grant")
if "Eclipse Project for Servlet" not in Path("NOTICE").read_text(encoding="utf-8"):
    raise SystemExit("NOTICE changed")
if list(Path(".").rglob("*.jar")) or list(Path(".").rglob("*.class")):
    raise SystemExit("prebuilt binary remains")
for pom in Path(".").rglob("pom.xml"):
    pom.unlink()

Path("pom.xml").write_text("""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>jakarta.servlet</groupId>
  <artifactId>jakarta.servlet-api</artifactId>
  <version>%{version}</version>
  <packaging>jar</packaging>
  <name>Jakarta Servlet</name>
  <description>Jakarta Servlet %{version} API, packaged without a parent POM.</description>
  <url>https://projects.eclipse.org/projects/ee4j.servlet</url>
  <licenses>
    <license>
      <name>EPL-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0</name>
      <url>https://www.eclipse.org/legal/epl-2.0/</url>
    </license>
  </licenses>
  <properties>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <maven.compiler.release>8</maven.compiler.release>
  </properties>
  <build>
    <plugins>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-compiler-plugin</artifactId>
        <version>3.12.1</version>
        <configuration>
          <release>8</release>
        </configuration>
      </plugin>
      <plugin>
        <groupId>org.apache.maven.plugins</groupId>
        <artifactId>maven-jar-plugin</artifactId>
        <version>3.3.0</version>
        <configuration>
          <archive>
            <manifestEntries>
              <Automatic-Module-Name>jakarta.servlet</Automatic-Module-Name>
              <Specification-Version>5.0</Specification-Version>
              <Implementation-Version>%{version}</Implementation-Version>
            </manifestEntries>
          </archive>
        </configuration>
      </plugin>
    </plugins>
  </build>
</project>
""", encoding="utf-8")
pom = Path("pom.xml").read_text(encoding="utf-8")
for needle in (
    "<artifactId>jakarta.servlet-api</artifactId>",
    "<Automatic-Module-Name>jakarta.servlet</Automatic-Module-Name>",
    "<version>%{version}</version>",
    "<release>8</release>",
    "</project.build.sourceEncoding>",
):
    if needle not in pom:
        raise SystemExit("pom missing " + needle)
if pom.count("<version>5.0.0</version>") != 1:
    raise SystemExit("version 5.0.0 count")
for needle in (
    "junit",
    "SNAPSHOT",
    "<source>",
    "<target>",
    "<parent>",
    "<groupId>org.eclipse.ee4j</groupId>",
    "felix",
    "maven-bundle-plugin",
    "<version>5.0</version>",
    "projectbuild.sourceEncoding",
):
    if needle in pom:
        raise SystemExit("pom still contains " + needle)
PY

%build -a
java --module-path target/jakarta.servlet-api-%{version}.jar --describe-module jakarta.servlet > module-describe.txt
grep -q '^jakarta.servlet@' module-describe.txt || { cat module-describe.txt; exit 1; }
grep -q ' automatic$' module-describe.txt || { cat module-describe.txt; exit 1; }
if grep -q 'jakarta.servlet.api' module-describe.txt; then
	cat module-describe.txt
	exit 1
fi
python - <<'PY'
import struct
import zipfile
from pathlib import Path
jar = Path("target/jakarta.servlet-api-%{version}.jar")
with zipfile.ZipFile(jar) as zf:
    names = set(zf.namelist())
    required = {
        "jakarta/servlet/AsyncContext.class",
        "jakarta/servlet/AsyncEvent.class",
        "jakarta/servlet/AsyncListener.class",
        "jakarta/servlet/DispatcherType.class",
        "jakarta/servlet/Filter.class",
        "jakarta/servlet/FilterChain.class",
        "jakarta/servlet/FilterConfig.class",
        "jakarta/servlet/FilterRegistration$Dynamic.class",
        "jakarta/servlet/FilterRegistration.class",
        "jakarta/servlet/GenericFilter.class",
        "jakarta/servlet/GenericServlet.class",
        "jakarta/servlet/HttpConstraintElement.class",
        "jakarta/servlet/HttpMethodConstraintElement.class",
        "jakarta/servlet/MultipartConfigElement.class",
        "jakarta/servlet/ReadListener.class",
        "jakarta/servlet/Registration$Dynamic.class",
        "jakarta/servlet/Registration.class",
        "jakarta/servlet/RequestDispatcher.class",
        "jakarta/servlet/Servlet.class",
        "jakarta/servlet/ServletConfig.class",
        "jakarta/servlet/ServletContainerInitializer.class",
        "jakarta/servlet/ServletContext.class",
        "jakarta/servlet/ServletContextAttributeEvent.class",
        "jakarta/servlet/ServletContextAttributeListener.class",
        "jakarta/servlet/ServletContextEvent.class",
        "jakarta/servlet/ServletContextListener.class",
        "jakarta/servlet/ServletException.class",
        "jakarta/servlet/ServletInputStream.class",
        "jakarta/servlet/ServletOutputStream.class",
        "jakarta/servlet/ServletRegistration$Dynamic.class",
        "jakarta/servlet/ServletRegistration.class",
        "jakarta/servlet/ServletRequest.class",
        "jakarta/servlet/ServletRequestAttributeEvent.class",
        "jakarta/servlet/ServletRequestAttributeListener.class",
        "jakarta/servlet/ServletRequestEvent.class",
        "jakarta/servlet/ServletRequestListener.class",
        "jakarta/servlet/ServletRequestWrapper.class",
        "jakarta/servlet/ServletResponse.class",
        "jakarta/servlet/ServletResponseWrapper.class",
        "jakarta/servlet/ServletSecurityElement.class",
        "jakarta/servlet/SessionCookieConfig.class",
        "jakarta/servlet/SessionTrackingMode.class",
        "jakarta/servlet/SingleThreadModel.class",
        "jakarta/servlet/UnavailableException.class",
        "jakarta/servlet/WriteListener.class",
        "jakarta/servlet/annotation/HandlesTypes.class",
        "jakarta/servlet/annotation/HttpConstraint.class",
        "jakarta/servlet/annotation/HttpMethodConstraint.class",
        "jakarta/servlet/annotation/MultipartConfig.class",
        "jakarta/servlet/annotation/ServletSecurity$EmptyRoleSemantic.class",
        "jakarta/servlet/annotation/ServletSecurity$TransportGuarantee.class",
        "jakarta/servlet/annotation/ServletSecurity.class",
        "jakarta/servlet/annotation/WebFilter.class",
        "jakarta/servlet/annotation/WebInitParam.class",
        "jakarta/servlet/annotation/WebListener.class",
        "jakarta/servlet/annotation/WebServlet.class",
        "jakarta/servlet/descriptor/JspConfigDescriptor.class",
        "jakarta/servlet/descriptor/JspPropertyGroupDescriptor.class",
        "jakarta/servlet/descriptor/TaglibDescriptor.class",
        "jakarta/servlet/http/Cookie.class",
        "jakarta/servlet/http/HttpFilter.class",
        "jakarta/servlet/http/HttpServlet.class",
        "jakarta/servlet/http/HttpServletMapping.class",
        "jakarta/servlet/http/HttpServletRequest$1.class",
        "jakarta/servlet/http/HttpServletRequest.class",
        "jakarta/servlet/http/HttpServletRequestWrapper.class",
        "jakarta/servlet/http/HttpServletResponse.class",
        "jakarta/servlet/http/HttpServletResponseWrapper.class",
        "jakarta/servlet/http/HttpSession.class",
        "jakarta/servlet/http/HttpSessionActivationListener.class",
        "jakarta/servlet/http/HttpSessionAttributeListener.class",
        "jakarta/servlet/http/HttpSessionBindingEvent.class",
        "jakarta/servlet/http/HttpSessionBindingListener.class",
        "jakarta/servlet/http/HttpSessionContext.class",
        "jakarta/servlet/http/HttpSessionEvent.class",
        "jakarta/servlet/http/HttpSessionIdListener.class",
        "jakarta/servlet/http/HttpSessionListener.class",
        "jakarta/servlet/http/HttpUpgradeHandler.class",
        "jakarta/servlet/http/HttpUtils.class",
        "jakarta/servlet/http/MappingMatch.class",
        "jakarta/servlet/http/NoBodyOutputStream.class",
        "jakarta/servlet/http/NoBodyResponse.class",
        "jakarta/servlet/http/Part.class",
        "jakarta/servlet/http/PushBuilder.class",
        "jakarta/servlet/http/WebConnection.class",
    }
    classes = {name for name in names if name.endswith(".class")}
    missing = sorted(required - classes)
    if missing:
        raise SystemExit("missing " + " ".join(missing))
    extra = sorted(classes - required)
    if extra:
        raise SystemExit("extra " + " ".join(extra))
    if "module-info.class" in names:
        raise SystemExit("named module appeared")
    for name in (
        "jakarta/servlet/LocalStrings.properties",
        "jakarta/servlet/http/LocalStrings.properties",
        "jakarta/servlet/resources/web-app_5_0.xsd",
        "jakarta/servlet/resources/web-app_2_2.dtd",
    ):
        if name not in names:
            raise SystemExit("jar missing " + name)
    schemas = [name for name in names if name.endswith(".xsd")]
    if len(schemas) != 38:
        raise SystemExit("schema count " + str(len(schemas)))
    manifest = zf.read("META-INF/MANIFEST.MF").decode("utf-8")
    if "Automatic-Module-Name: jakarta.servlet" not in manifest:
        raise SystemExit("automatic module name missing")
    data = zf.read("jakarta/servlet/Servlet.class")
    major = struct.unpack(">H", data[6:8])[0]
    if major != 52:
        raise SystemExit("Servlet class version " + str(major))
PY

%install -a
mkdir -p %{buildroot}%{_datadir}/java/modules
ln -s ../jakarta-servlet-api.jar %{buildroot}%{_datadir}/java/modules/jakarta.servlet-%{version}.jar
ln -s jakarta-servlet-api.jar %{buildroot}%{_datadir}/java/jakarta.servlet-api-%{version}.jar

%files -f .mfiles
%doc LICENSE NOTICE
%{_datadir}/java/jakarta.servlet-api-%{version}.jar
%{_datadir}/java/modules/jakarta.servlet-%{version}.jar
