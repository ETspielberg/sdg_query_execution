<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:dc="http://dublincore.org/documents/dcmi-namespace/"
                xmlns:aqd="http://aurora-network.global/queries/namespace/"
                exclude-result-prefixes="xsl aqd dc">

    <xsl:template match="/">
        <html>
            <head>
                <meta charset="utf-8"/>
                <meta http-equiv="X-UA-Compatible" content="IE=edge"/>
                <meta name="viewport" content="width=device-width, initial-scale=1"/>
                <!-- The above 3 meta tags *must* come first in the head; any other head
                    content must come *after* these tags -->
                <meta name="description" content=""/>
                <meta name="author" content=""/>
                <!-- <link rel="icon" href="img/favicon.ico" /> -->
                <title>Aurora SDG queries</title>
                <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css"
                      integrity="sha384-HSMxcRTRxnN+Bdg0JdbxYKrThecOKuH5zCYotlSAcp1+c8xmyTe9GYg1l9a69psu"
                      crossorigin="anonymous"></link>
                <!-- <script src="https://stackpath.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"
                        integrity="sha384-aJ21OjlMXNL5UyIl/XNwTMqvzeRMZH2w8c5cRVpzpU8Y5bApTppSuUkhZXN0VxHd"
                        crossorigin="anonymous" ></script>-->
            </head>
            <body>
                <div class="jumbotron">
                    <div class="container">
                        <h1>Aurora SDG Queries</h1>
                        <p>SDG analysis: Biliometrics of Relevance</p>
                    </div>
                </div>
                <div class="container">
                    <xsl:apply-templates select="aqd:query"/>
                </div>
            </body>
        </html>
    </xsl:template>

    <xsl:template match="aqd:queries">
        <xsl:apply-templates select="aqd:query"/>
    </xsl:template>

    <xsl:template match="aqd:query">
        <h2>
            <xsl:value-of select="dc:title/."/>
        </h2>
        <p>
            <xsl:value-of select="dc:description"/>
        </p>
        <p>
            Last updated:
            <xsl:value-of select="dc:date-modified"/>
        </p>
        <xsl:apply-templates select="aqd:query-definitions"/>
    </xsl:template>

    <xsl:template match="aqd:query-definitions">
        <table class="table table-striped" border="1">
            <thead>
                <tr bgcolor="#9acd32">
                    <th>Target</th>
                    <th>Description</th>
                    <th>Query</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td/>
                    <td/>
                    <td>
                        (
                    </td>
                </tr>
                <xsl:apply-templates select="aqd:query-definition" mode="table"/>
                <tr>
                    <td/>
                    <td/>
                    <td>
                        )
                    </td>
                </tr>
                <tr>
                    <td></td>
                    <td>Filter:</td>
                    <td>
                        <xsl:apply-templates select="aqd:filters"/>
                    </td>
                </tr>
            </tbody>
        </table>

        <div>
            (<xsl:apply-templates select="aqd:query-definition" mode="query"/>)
            <xsl:apply-templates select="aqd:filters"/>
        </div>
    </xsl:template>

    <xsl:template match="aqd:query-definition" mode="table">
        <tr>
            <td>
                <xsl:value-of select="../../dc:identifier"/>.
                <xsl:value-of select="aqd:subquery-identifier"/>
            </td>
            <td>
                <xsl:apply-templates select="aqd:subquery-descriptions"/>
            </td>
            <td>
                <xsl:if test="count(aqd:query-lines/aqd:query-line) > 0">
                    <xsl:if test="aqd:query-lines/aqd:query-line/. != ''">
                        <xsl:if test="position() != 1">
                            <xsl:text>OR</xsl:text>
                        </xsl:if>
                        <xsl:apply-templates select="aqd:query-lines"/>
                        <xsl:apply-templates select="aqd:filters"/>
                    </xsl:if>
                </xsl:if>
            </td>
        </tr>
    </xsl:template>

    <xsl:template match="aqd:query-definition" mode="query">
        <xsl:if test="count(aqd:query-lines/aqd:query-line) > 0">
            <xsl:if test="aqd:query-lines/aqd:query-line/. != ''">
                <xsl:if test="position() != 1">
                    <xsl:text>OR</xsl:text>
                </xsl:if>
                <xsl:apply-templates select="aqd:query-lines"/>
                <xsl:apply-templates select="aqd:filters"/>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <xsl:template match="aqd:subquery-descriptions">
        <xsl:apply-templates select="aqd:subquery-description"/>
    </xsl:template>

    <xsl:template match="aqd:subquery-description">
        <p>
            <xsl:value-of select="."/>
        </p>
    </xsl:template>

    <xsl:template match="aqd:query-lines">
        <font face="arial,helvetica">
            <xsl:if test="@field">
                <xsl:value-of select="@field"/>(
            </xsl:if>
            <xsl:apply-templates select="aqd:query-line"/>
            <xsl:if test="@field">
                )
            </xsl:if>
        </font>
    </xsl:template>

    <xsl:template match="aqd:query-line">
        <p>
            <font face="arial,helvetica">
                <xsl:if test="@field">
                    <xsl:value-of select="@field"/>
                </xsl:if>
                (<xsl:value-of select="."/>)
                <xsl:if test="position() != last()">
                    <xsl:text> OR </xsl:text>
                    <xsl:text>&#xa;</xsl:text>
                </xsl:if>
            </font>
        </p>
    </xsl:template>

    <xsl:template match="aqd:filters">
        <xsl:if test="aqd:timerange">
            <p>
                <font face="arial,helvetica">
                     AND (
                    <xsl:value-of select="aqd:timerange/@field"/>
                    &gt;
                    <xsl:value-of select="aqd:timerange/aqd:start/."/>
                     AND
                    <xsl:value-of select="aqd:timerange/@field"/>
                    &lt;
                    <xsl:value-of select="aqd:timerange/aqd:end/."/>
                    )
                </font>
            </p>
        </xsl:if>
        <xsl:if test="aqd:filter">
            <xsl:if test="aqd:filter !=''">
                <font face="arial,helvetica">
                    <xsl:if test="position() != last()">
                        AND
                    </xsl:if>
                    <p>
                        (<xsl:apply-templates select="aqd:filter"/>)
                    </p>
                </font>
            </xsl:if>
        </xsl:if>
    </xsl:template>

    <xsl:template match="aqd:filter">
        <font face="arial,helvetica">
            <xsl:value-of select="@field"/>(<xsl:value-of select="."/>)
        </font>
    </xsl:template>
</xsl:stylesheet>