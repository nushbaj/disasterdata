import React, { useEffect, useState } from "react";
import WordCloud from "react-d3-cloud";
import { Card } from "react-bootstrap";
import { scaleLinear } from "d3-scale";

const API_HOST = "https://api.disasterdata.duckdns.org";

const KeywordCloud = () => {
    const [words, setWords] = useState([]);

    useEffect(() => {
        fetch(API_HOST + "/fetch-most-frequent-word/")
            .then((response) => response.json())
            .then((data) => {
                if (data) {
                    const formattedWords = data.map(({ count, keyword }) => ({
                        value: count,
                        text: keyword,
                    }));
                    setWords(formattedWords);
                }
            })
            .catch((error) => console.error("Error fetching word cloud data:", error));
    }, []);

    const fontScale = scaleLinear()
        .domain([Math.min(...words.map((d) => d.value)), Math.max(...words.map((d) => d.value))])
        .range([10, 60]); // Min and max font sizes
    const fontSize = (word) => fontScale(word.value);

    return (
        <Card className="shadow-sm" style={{ height: "300px", margin: "auto" }}>
            <Card.Body>
                <Card.Title>Keyword Cloud</Card.Title>
                {words.length > 0 ? <WordCloud data={words} fontSize={fontSize} rotate={0} padding={2} width={300} height={100} /> : <p>Loading keyword cloud...</p>}
            </Card.Body>
        </Card>
    );
};

export default KeywordCloud;
